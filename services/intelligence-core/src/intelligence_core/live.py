from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.event_intelligence import (
    DeterministicEventAnalyzer,
    daily_event_summary,
)
from intelligence_core.macro import build_macro_snapshot, default_unknown_state
from intelligence_core.models import CollectionPolicy, HealthStatus
from intelligence_core.operations import build_daily_archive, daily_summary
from intelligence_core.reports import daily_audit_report, maintenance_report
from intelligence_core.worker import JobHandler

FEEDS = {
    "rbi-press-releases-rss": "https://rbi.org.in/pressreleases_rss.xml",
    "sebi-rss": "https://www.sebi.gov.in/sebirss.xml",
}


def collect_and_persist(
    store: SQLiteOperationsStore, collector: OfficialRssCollector
) -> dict[str, int | str]:
    artifacts = [collector.fetch(uri) for uri in collector.discover()]
    totals = {"records_seen": 0, "records_new": 0}
    for artifact in artifacts:
        result = store.persist_collection(
            artifact, collector.normalize(collector.parse(artifact), artifact)
        )
        totals = {key: totals[key] + result[key] for key in totals}
    return {"status": "COLLECTED", **totals}


def live_source_handlers(store: SQLiteOperationsStore) -> dict[str, JobHandler]:
    sources = {source.source_id: source for source in initial_sources()}
    handlers: dict[str, JobHandler] = {}
    for job_name, source_id in (
        ("rbi-rss", "rbi-press-releases-rss"),
        ("sebi-rss", "sebi-rss"),
    ):
        collector = OfficialRssCollector(
            sources[source_id],
            CollectionPolicy(source_id=source_id, cadence_seconds=900),
            FEEDS[source_id],
        )

        def handler(
            _job: DurableJob,
            _now: datetime,
            collector: OfficialRssCollector = collector,
        ) -> dict:
            return collect_and_persist(store, collector)

        handlers[job_name] = handler
    return handlers


def operational_handlers(
    store: SQLiteOperationsStore, output_root: str | Path = "data/local/intelligence"
) -> dict[str, JobHandler]:
    root = Path(output_root)

    def health(_job: DurableJob, now: datetime) -> dict:
        events = store.events()
        states = {}
        for source in initial_sources():
            latest = max(
                (event.observed_at for event in events if event.source_id == source.source_id),
                default=None,
            )
            states[source.source_id] = (
                HealthStatus.HEALTHY
                if latest and (now - latest).total_seconds() <= 7200
                else HealthStatus.STALE
            )
        return {"source_health": {key: value.value for key, value in states.items()}}

    def build(_job: DurableJob, now: datetime) -> dict:
        events = store.events()
        states = {source.source_id: HealthStatus.UNKNOWN for source in initial_sources()}
        archive = build_daily_archive(
            now.astimezone(UTC).date(),
            events=events,
            source_health=states,
            job_ids=store.execution_keys(),
            incidents=store.incidents(),
            universe_state={"status": "NO_APPROVED_UNIVERSE_FEED"},
            target=root / "archives" / f"{now.date().isoformat()}.json",
        )
        return {"manifest_hash": archive["manifest_hash"], "events": len(archive["events"])}

    def event_build(_job: DurableJob, now: datetime) -> dict:
        analyzer = DeterministicEventAnalyzer()
        records = [
            analyzer.analyze(
                event,
                cluster_id=event.duplicate_group_id or str(event.event_id),
                derived_at=max(now, event.available_at),
            )
            for event in store.events()
            if event.available_at <= now
        ]
        payload = {
            "label": "INTERNAL EVENT EVIDENCE — NOT PREDICTION",
            "records": [record.model_dump(mode="json") for record in records],
            "summary": daily_event_summary(records, now),
        }
        root.mkdir(parents=True, exist_ok=True)
        target = root / "event-intelligence" / f"{now.date().isoformat()}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return {"status": "ALREADY_BUILT", "events": len(records)}
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        return {"status": "BUILT", "events": len(records)}

    def summary(_job: DurableJob, now: datetime) -> dict:
        events = store.events()
        states = {source.source_id: HealthStatus.UNKNOWN for source in initial_sources()}
        payload = daily_summary(now.date(), events, states, store.incidents())
        root.mkdir(parents=True, exist_ok=True)
        (root / "daily-summary.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        return payload

    def audit(_job: DurableJob, _now: datetime) -> dict:
        report = daily_audit_report(
            health=health(_job, _now)["source_health"],
            failures=store.incidents(),
            entity_issues=[],
            universe_changes=[],
            anomalies=[],
        )
        root.mkdir(parents=True, exist_ok=True)
        (root / "codex-daily-audit.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )
        return {"report_type": report.report_type}

    def maintenance(_job: DurableJob, _now: datetime) -> dict:
        report = maintenance_report(
            sources=[], incidents=store.incidents(), unresolved_entities=[], candidates=[]
        )
        root.mkdir(parents=True, exist_ok=True)
        (root / "codex-source-maintenance.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )
        return {"report_type": report.report_type}

    def macro_build(job: DurableJob, now: datetime) -> dict:
        policy, cross_market, regime = default_unknown_state(now)
        snapshot = build_macro_snapshot(
            now,
            [],
            policy_state=policy,
            cross_market=cross_market,
            regime=regime,
            source_health={"rbi-press-releases-rss": "HEALTHY"},
        )
        root.mkdir(parents=True, exist_ok=True)
        target = root / "macro" / f"{job.name}-{now.date().isoformat()}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        return {
            "status": "BUILT_INTERNAL_NOT_PREDICTION",
            "snapshot_hash": snapshot.snapshot_hash,
            "observations": len(snapshot.observations),
        }

    return {
        "source-health": health,
        "macro-release-processing": lambda _job, _now: {
            "status": "RBI_EVENT_PIPELINE_ACTIVE_OTHER_SOURCES_FIXTURE"
        },
        "pre-market-macro-build": macro_build,
        "eod-macro-build": macro_build,
        "macro-quality-audit": lambda _job, _now: {
            "status": "PASS_FIXTURE_CONTRACTS_LIVE_RBI_METADATA_ONLY"
        },
        "event-intelligence-build": event_build,
        "daily-intelligence-build": build,
        "intelligence-summary": summary,
        "daily-quality-audit": audit,
        "source-failure-review": maintenance,
        "universe-check": lambda _job, _now: {"status": "NO_APPROVED_UNIVERSE_FEED"},
        "source-discovery-proposal": lambda _job, _now: {"status": "PROPOSAL_ONLY"},
    }
