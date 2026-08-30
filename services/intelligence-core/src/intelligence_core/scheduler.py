from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from intelligence_core.collectors import CollectorError, IntelligenceCollector, RawArtifact
from intelligence_core.models import CollectionMode, CollectionPolicy, JobLedgerEntry
from intelligence_core.processing import CircuitBreaker


@dataclass(frozen=True)
class ScheduledJob:
    name: str
    source_id: str
    schedule_type: str
    cadence_seconds: int | None = None
    market_session: str | None = None
    event_trigger: str | None = None


class LocalScheduler:
    def __init__(self) -> None:
        self.jobs: dict[str, ScheduledJob] = {}

    def register(self, job: ScheduledJob) -> None:
        if job.name in self.jobs:
            raise ValueError("duplicate scheduled job")
        if job.schedule_type not in {"CRON", "INTERVAL", "MARKET_SESSION", "EVENT", "MANUAL"}:
            raise ValueError("unsupported schedule type")
        self.jobs[job.name] = job

    def due(self, _at: datetime) -> tuple[ScheduledJob, ...]:
        return tuple(self.jobs[name] for name in sorted(self.jobs))


class CollectionRunner:
    def __init__(self) -> None:
        self.raw_artifacts: dict[str, RawArtifact] = {}
        self.events: dict[str, object] = {}
        self.ledger: list[JobLedgerEntry] = []
        self.breakers: dict[str, CircuitBreaker] = {}

    def run(
        self,
        collector: IntelligenceCollector,
        policy: CollectionPolicy,
        *,
        mode: CollectionMode,
        code_sha: str = "UNKNOWN",
    ) -> JobLedgerEntry:
        source = collector.source_metadata()
        breaker = self.breakers.setdefault(
            source.source_id, CircuitBreaker(policy.failure_threshold)
        )
        started = datetime.now(UTC)
        seen = new = duplicates = failed = raw_count = canonical = 0
        error_summary = None
        if breaker.opened:
            return self._record(source.source_id, mode, started, "CIRCUIT_OPEN", code_sha=code_sha)
        try:
            for uri in collector.discover()[: policy.maximum_requests]:
                artifact = collector.fetch(uri)
                raw_count += 1
                self.raw_artifacts.setdefault(artifact.sha256, artifact)
                parsed = collector.parse(artifact)
                seen += len(parsed)
                for event in collector.normalize(parsed, artifact):
                    key = event.source_event_id or event.raw_payload_hash + event.title
                    if key in self.events:
                        duplicates += 1
                    else:
                        self.events[key] = event
                        new += 1
                        canonical += 1
            breaker.record_success()
            status = "SUCCEEDED"
        except (CollectorError, ValueError) as error:
            breaker.record_failure()
            failed += 1
            error_summary = type(error).__name__
            status = "FAILED" if not breaker.opened else "CIRCUIT_OPENED"
        entry = JobLedgerEntry(
            source_id=source.source_id,
            mode=mode,
            scheduled_for=started,
            started_at=started,
            ended_at=datetime.now(UTC),
            status=status,
            records_seen=seen,
            records_new=new,
            records_duplicate=duplicates,
            records_failed=failed,
            raw_artifacts=raw_count,
            canonical_events=canonical,
            error_summary=error_summary,
            collector_version=source.collector_version,
            code_sha=code_sha,
        )
        self.ledger.append(entry)
        return entry

    def _record(
        self, source_id: str, mode: CollectionMode, started: datetime, status: str, *, code_sha: str
    ) -> JobLedgerEntry:
        entry = JobLedgerEntry(
            source_id=source_id,
            mode=mode,
            scheduled_for=started,
            started_at=started,
            ended_at=datetime.now(UTC),
            status=status,
            code_sha=code_sha,
        )
        self.ledger.append(entry)
        return entry
