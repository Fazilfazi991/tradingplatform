from __future__ import annotations

import os
import signal
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import FrameType
from uuid import uuid4

from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.models import (
    IntelligenceIncident,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)

JobHandler = Callable[[DurableJob, datetime], dict]


class JobDeadlineExceeded(TimeoutError):
    pass


@contextmanager
def enforced_deadline(seconds: float) -> Iterator[bool]:
    """Interrupt Python handlers on the Linux production host.

    Windows has no SIGALRM; its local runtime retains post-return timeout detection and must rely on
    the documented process supervisor for hard termination.
    """
    supported = (
        os.name == "posix"
        and threading.current_thread() is threading.main_thread()
        and hasattr(signal, "setitimer")
    )
    if not supported:
        yield False
        return

    def expire(_signum: int, _frame: FrameType | None) -> None:
        raise JobDeadlineExceeded("job deadline exceeded")

    # Dynamic lookup keeps this module importable/type-checkable on Windows, where these names do
    # not exist; the production branch above has already established POSIX support.
    sigalrm = getattr(signal, "SIGALRM")  # noqa: B009
    setitimer = getattr(signal, "setitimer")  # noqa: B009
    itimer_real = getattr(signal, "ITIMER_REAL")  # noqa: B009
    previous_handler = signal.getsignal(sigalrm)
    signal.signal(sigalrm, expire)
    previous_timer = setitimer(itimer_real, seconds)
    try:
        yield True
    finally:
        setitimer(itimer_real, 0)
        signal.signal(sigalrm, previous_handler)
        if previous_timer[0] > 0:
            setitimer(itimer_real, previous_timer[0], previous_timer[1])


class IntelligenceWorker:
    def __init__(
        self,
        store: SQLiteOperationsStore,
        handlers: dict[str, JobHandler],
        *,
        mode: IntelligenceRuntimeMode,
        owner: str | None = None,
        lock_ttl: timedelta = timedelta(minutes=10),
        job_timeout_seconds: float = 120,
        validate_handlers: bool = True,
    ) -> None:
        IntelligenceRuntimePolicy.authorize(mode)
        self.store = store
        self.handlers = handlers
        self.mode = mode
        self.owner = owner or str(uuid4())
        self.lock_ttl = lock_ttl
        self.job_timeout_seconds = job_timeout_seconds
        self.shutdown = threading.Event()
        if validate_handlers:
            missing = sorted(job.name for job in store.all_jobs() if job.name not in handlers)
            if missing:
                for name in missing:
                    self.store.record_incident(
                        IntelligenceIncident(
                            incident_type="SCHEDULER_HANDLER_MISSING",
                            severity="CRITICAL",
                            evidence={"job": name},
                            affected_data=(name,),
                        )
                    )
                raise ValueError(f"missing required job handlers: {', '.join(missing)}")

    def request_shutdown(self, *_args) -> None:
        self.shutdown.set()

    def install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def run_once(self, *, now: datetime | None = None) -> list[dict]:
        now = (now or datetime.now(UTC)).astimezone(UTC)
        results = []
        for job in self.store.due_jobs(now):
            if self.shutdown.is_set():
                break
            lateness = (now - job.next_run_at).total_seconds()
            if lateness > 3600 and not self.store.has_open_incident("SCHEDULER_MISSED_RUN"):
                self.store.record_incident(
                    IntelligenceIncident(
                        incident_type="SCHEDULER_MISSED_RUN",
                        severity="WARNING",
                        evidence={"job": job.name, "lateness_seconds": lateness},
                        affected_data=(job.name,),
                    )
                )
            if not self.store.acquire(job.name, self.owner, now=now, ttl=self.lock_ttl):
                continue
            key = self.store.begin_execution(job, now)
            if key is None:
                self.store.release(job.name, self.owner)
                continue
            started = time.perf_counter()
            status = "SUCCEEDED"
            try:
                handler = self.handlers[job.name]
                with enforced_deadline(self.job_timeout_seconds) as deadline_enforced:
                    result = handler(job, now)
                if lateness <= 3600:
                    self.store.resolve_open_incidents(
                        "SCHEDULER_MISSED_RUN",
                        source_id=None,
                        now=now,
                        resolution="SCHEDULED_EXECUTION_RETURNED_WITHIN_TOLERANCE",
                        affected_data=job.name,
                    )
                if job.source_id:
                    self.store.resolve_open_incidents(
                        "SOURCE_COLLECTION_FAILURE",
                        source_id=job.source_id,
                        now=now,
                        resolution="SOURCE_COLLECTION_RECOVERED",
                    )
                elapsed = time.perf_counter() - started
                if elapsed > self.job_timeout_seconds:
                    status = "TIMED_OUT"
                    self.store.record_incident(
                        IntelligenceIncident(
                            incident_type="SCHEDULER_JOB_TIMEOUT",
                            severity="HIGH",
                            source_id=job.source_id,
                            evidence={
                                "job": job.name,
                                "elapsed_seconds": elapsed,
                                "timeout_seconds": self.job_timeout_seconds,
                                "enforcement": (
                                    "SIGNAL_ENFORCED"
                                    if deadline_enforced
                                    else "COOPERATIVE_LOCAL_FALLBACK"
                                ),
                            },
                            affected_data=(job.name,),
                        )
                    )
            except JobDeadlineExceeded:
                elapsed = time.perf_counter() - started
                status = "TIMED_OUT"
                result = {"error": "JobDeadlineExceeded"}
                self.store.record_incident(
                    IntelligenceIncident(
                        incident_type="SCHEDULER_JOB_TIMEOUT",
                        severity="HIGH",
                        source_id=job.source_id,
                        evidence={
                            "job": job.name,
                            "elapsed_seconds": elapsed,
                            "timeout_seconds": self.job_timeout_seconds,
                            "enforcement": "SIGNAL_ENFORCED",
                        },
                        affected_data=(job.name,),
                    )
                )
            except Exception as error:  # noqa: BLE001 - worker boundary sanitizes and records failures
                status = "FAILED"
                result = {"error": type(error).__name__}
                self.store.record_incident(
                    IntelligenceIncident(
                        incident_type=(
                            "SOURCE_COLLECTION_FAILURE"
                            if job.source_id
                            else "SCHEDULER_JOB_FAILURE"
                        ),
                        severity="HIGH",
                        source_id=job.source_id,
                        evidence={"job": job.name, "error_class": type(error).__name__},
                        affected_data=(job.name,),
                    )
                )
            try:
                self.store.finish_execution(
                    key, job, now=datetime.now(UTC), status=status, result=result
                )
            finally:
                self.store.release(job.name, self.owner)
            results.append({"job": job.name, "status": status, **result})
        return results

    def run_forever(self, *, poll_seconds: float = 5) -> None:
        self.install_signal_handlers()
        self.store.start_service(self.owner, os.getpid(), now=datetime.now(UTC))
        try:
            self.store.heartbeat_service(self.owner, now=datetime.now(UTC))
            while not self.shutdown.wait(poll_seconds):
                if self.store.service_stop_requested(self.owner):
                    self.shutdown.set()
                    break
                self.store.heartbeat_service(self.owner, now=datetime.now(UTC))
                self.run_once()
        finally:
            self.store.stop_service(self.owner, now=datetime.now(UTC))


def default_store(workspace: str | Path) -> SQLiteOperationsStore:
    return SQLiteOperationsStore(Path(workspace) / "data/local/intelligence-operations.sqlite3")
