from __future__ import annotations

import signal
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.models import (
    IntelligenceIncident,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)

JobHandler = Callable[[DurableJob, datetime], dict]


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
            if lateness > 3600:
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
                result = handler(job, now)
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
                                "note": "cooperative timeout detected after handler return",
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
                self.store.finish_execution(key, job, now=now, status=status, result=result)
            finally:
                self.store.release(job.name, self.owner)
            results.append({"job": job.name, "status": status, **result})
        return results

    def run_forever(self, *, poll_seconds: float = 5) -> None:
        self.install_signal_handlers()
        while not self.shutdown.wait(poll_seconds):
            self.run_once()


def default_store(workspace: str | Path) -> SQLiteOperationsStore:
    return SQLiteOperationsStore(Path(workspace) / "data/local/intelligence-operations.sqlite3")
