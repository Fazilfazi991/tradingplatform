from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.event_intelligence import SAFE_PROMPT_VERSION
from intelligence_core.forensic_worker import ForensicSemanticProcessor
from intelligence_core.llm_analyzer import (
    AnalyzerTask,
    LLMAnalysisResult,
    OpenAIResponsesAdapter,
    ProviderConfig,
)
from intelligence_core.models import CollectionPolicy, IntelligenceIncident, IntelligenceRuntimeMode
from intelligence_core.runtime_forensics import (
    CollectionAttemptRecord,
    ForensicRuntimeStore,
    TerminalDisposition,
    TransportStatus,
)
from intelligence_core.soak_operations import (
    AlertThresholds,
    SoakManifest,
    full_content_access_state,
    manifest_hash,
)
from intelligence_core.worker import IntelligenceWorker
from research_core.common import stable_hash

FEEDS = {
    "rbi-press-releases-rss": "https://rbi.org.in/pressreleases_rss.xml",
    "sebi-rss": "https://www.sebi.gov.in/sebirss.xml",
}
INPUT_PRICE, OUTPUT_PRICE = 0.20, 1.20
SOAK_PROMPT_VERSION = f"{SAFE_PROMPT_VERSION}-soak-v1"
RETRY_POLICY_VERSION = "structured-bounded-v1"
SEMANTIC_POLICY_VERSION = "normalized-title-content-published-source-event-v1"
CACHE_POLICY_VERSION = "validated-success-semantic-policy-v1"


def load_local_env(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def current_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def build_manifest(
    config: dict[str, Any], *, now: datetime, model: str, soak_id: str
) -> SoakManifest:
    sources = initial_sources()
    values = {
        "version": soak_id,
        "started_at": now,
        "target_end_at": now + timedelta(hours=float(config["target_duration_hours"])),
        "model": model,
        "prompt_version": SOAK_PROMPT_VERSION,
        "schema_hash": manifest_hash(LLMAnalysisResult.model_json_schema()),
        "routing_hash": manifest_hash({task.value: ["openai"] for task in AnalyzerTask}),
        "config_hash": manifest_hash(config),
        "code_sha": current_sha(),
        "source_registry_version": "initial-sources-v1",
        "source_registry_hash": manifest_hash(
            [source.model_dump(mode="json") for source in sources]
        ),
        "collector_versions_hash": manifest_hash({"official_rss_collector": "1", "parser": "1"}),
        "budget_policy_hash": manifest_hash(config["budget"]),
        "retry_policy_hash": manifest_hash(RETRY_POLICY_VERSION),
        "semantic_identity_policy_hash": manifest_hash(SEMANTIC_POLICY_VERSION),
        "cache_policy_hash": manifest_hash(CACHE_POLICY_VERSION),
    }
    values["soak_manifest_hash"] = manifest_hash(values)
    return SoakManifest.model_validate(values)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def daily_spend(store: ForensicRuntimeStore, day: datetime) -> float:
    return sum(
        row.estimated_total_cost
        for row in store.attempts()
        if row.completed_at.date() == day.date()
    )


def main() -> None:
    workspace = Path.cwd()
    load_local_env(workspace / ".env")
    config_path = workspace / "config/live-intelligence-soak.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["target_duration_hours"] != 24 or config["mode"] != "INTERNAL_LIVE":
        raise SystemExit("REAL_24H_INTERNAL_LIVE_CONFIGURATION_REQUIRED")
    if config["prediction_authorized"] or config["research_mode"] != "ENGINEERING_FIXTURE":
        raise SystemExit("PREDICTION_OR_RESEARCH_GATE_CHANGED")
    api_key, model = os.environ.get("OPENAI_API_KEY", ""), os.environ.get("OPENAI_MODEL", "")
    if not api_key or not model:
        raise SystemExit("OPENAI_CONFIGURATION_MISSING")

    soak_id = os.environ.get("QUALIFYING_SOAK_ID", config["version"])
    local = workspace / "data/local"
    database = local / f"{soak_id}.sqlite3"
    manifest_path, status_path = (
        local / f"{soak_id}-manifest.json",
        local / f"{soak_id}-status.json",
    )
    operations, forensics = SQLiteOperationsStore(database), ForensicRuntimeStore(database)
    now = datetime.now(UTC)
    candidate = build_manifest(config, now=now, model=model, soak_id=soak_id)
    if manifest_path.exists():
        manifest = SoakManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        comparison = candidate.model_copy(
            update={
                "started_at": manifest.started_at,
                "target_end_at": manifest.target_end_at,
                "soak_manifest_hash": manifest.soak_manifest_hash,
            }
        )
        manifest.assert_frozen(comparison)
    else:
        manifest = candidate
        write_json(manifest_path, manifest.model_dump(mode="json"))
    operations.recover_interrupted(now)
    operations.load_config(config_path, now=now)

    provider = ProviderConfig(
        provider="openai",
        model=model,
        model_version="runtime-frozen",
        enabled=True,
        max_output_tokens=600,
        timeout_seconds=45,
        input_cost_per_million=INPUT_PRICE,
        output_cost_per_million=OUTPUT_PRICE,
    )
    sources = {source.source_id: source for source in initial_sources()}
    thresholds = AlertThresholds.model_validate(config["alert_thresholds"])
    daily_budget = float(config["budget"]["daily_usd"])
    processor = ForensicSemanticProcessor(
        store=forensics,
        adapter=OpenAIResponsesAdapter(api_key=api_key),
        provider_config=provider,
        prompt_version=SOAK_PROMPT_VERSION,
        schema_version="llm-analysis-result-v1",
        schema_hash=manifest.schema_hash,
        routing_version="openai-primary-v1",
        configuration_hash=manifest.config_hash,
        retry_policy_version=RETRY_POLICY_VERSION,
    )
    incident_markers: set[str] = set()
    qualifying = True

    def record_once(kind: str, severity: str, evidence: dict[str, Any]) -> None:
        if kind not in incident_markers:
            operations.record_incident(
                IntelligenceIncident(
                    incident_type=cast(Any, kind),
                    severity=cast(Literal["INFO", "WARNING", "HIGH", "CRITICAL"], severity),
                    evidence=evidence,
                    affected_data=(soak_id,),
                )
            )
            incident_markers.add(kind)

    def record_collection(
        job: DurableJob,
        ordinal: int,
        started: datetime,
        perf: float,
        *,
        status: TransportStatus,
        handler: str,
        parse: str,
        terminal: str,
        error: Exception | None = None,
        records_seen: int = 0,
        canonical: int = 0,
        duplicates: int = 0,
        recovered: bool = False,
    ) -> None:
        forensics.add_collection_attempt(
            CollectionAttemptRecord(
                attempt_id=uuid4(),
                job_id=f"{job.name}:{job.next_run_at.isoformat()}",
                source_id=job.source_id or "UNKNOWN",
                scheduled_for=job.next_run_at,
                started_at=started,
                completed_at=datetime.now(UTC),
                attempt_ordinal=ordinal,
                transport_status=status,
                error_class=type(error).__name__ if error else None,
                handler_status=handler,
                parse_status=parse,
                records_seen=records_seen,
                canonical_events=canonical,
                duplicate_count=duplicates,
                recovered=recovered,
                terminal_job_status=terminal,
                latency_ms=(time.perf_counter() - perf) * 1000,
                provenance_hash=stable_hash(
                    {
                        "job": job.name,
                        "scheduled": job.next_run_at,
                        "attempt": ordinal,
                        "status": status,
                    }
                ),
            )
        )

    def collect(job: DurableJob, cycle_at: datetime) -> dict[str, Any]:
        if not job.source_id:
            return {"status": "NO_SOURCE"}
        source = sources[job.source_id]
        collector = OfficialRssCollector(
            source,
            CollectionPolicy(source_id=source.source_id, cadence_seconds=900, timeout_seconds=15),
            FEEDS[source.source_id],
        )
        events: list[Any] = []
        persisted = {"records_seen": 0, "records_new": 0}
        for ordinal in (1, 2):
            started, perf = datetime.now(UTC), time.perf_counter()
            try:
                artifact = collector.fetch(collector.discover()[0])
            except Exception as error:  # noqa: BLE001
                record_collection(
                    job,
                    ordinal,
                    started,
                    perf,
                    status=TransportStatus.FAILED,
                    handler="FAILED",
                    parse="NOT_RUN",
                    terminal="PENDING" if ordinal == 1 else "FAILED",
                    error=error,
                )
                if ordinal == 2:
                    record_once(
                        "SOURCE_COLLECTION_FAILURE",
                        "HIGH",
                        {"source_id": source.source_id, "error_class": type(error).__name__},
                    )
                    return {"status": "FAILED", "error_class": type(error).__name__}
                continue
            try:
                events = collector.normalize(collector.parse(artifact), artifact)
                persisted = operations.persist_collection(artifact, events)
            except Exception as error:  # noqa: BLE001
                record_collection(
                    job,
                    ordinal,
                    started,
                    perf,
                    status=TransportStatus.SUCCEEDED,
                    handler="FAILED",
                    parse="FAILED",
                    terminal="PENDING" if ordinal == 1 else "FAILED",
                    error=error,
                )
                if ordinal == 2:
                    record_once(
                        "SOURCE_COLLECTION_FAILURE",
                        "HIGH",
                        {"source_id": source.source_id, "error_class": type(error).__name__},
                    )
                    return {"status": "FAILED", "error_class": type(error).__name__}
                continue
            record_collection(
                job,
                ordinal,
                started,
                perf,
                status=TransportStatus.SUCCEEDED,
                handler="SUCCEEDED",
                parse="PASS",
                terminal="SUCCEEDED",
                records_seen=len(events),
                canonical=persisted["records_new"],
                duplicates=len(events) - persisted["records_new"],
                recovered=ordinal > 1,
            )
            break

        counters: Counter[str] = Counter()
        for event in events:
            event_id = f"{event.source_id}:{event.source_event_id}"
            if daily_spend(forensics, cycle_at) >= daily_budget:
                forensics.set_disposition(
                    event_id=event_id,
                    semantic_id=None,
                    disposition=TerminalDisposition.NOT_ANALYZED_BY_POLICY,
                    detail={
                        "reason": "DAILY_BUDGET_EXHAUSTED",
                        "cache_state": "NOT_CHECKED",
                        "tombstone_state": "NOT_CHECKED",
                        "downstream_state": "PENDING_ANALYSIS",
                    },
                )
                counters["pending_analysis"] += 1
                record_once("LLM_COST_BUDGET_EXCEEDED", "HIGH", {"daily_budget_usd": daily_budget})
                continue
            outcome = processor.process(
                event_id=event_id,
                source_id=event.source_id,
                source_artifact_hash=event.raw_payload_hash,
                title=event.title,
                content=event.summary,
                published_at=event.published_at,
                task=AnalyzerTask.RBI_POLICY_INTERPRETATION
                if event.source_id.startswith("rbi")
                else AnalyzerTask.EVENT_CLASSIFICATION,
                now=cycle_at,
            )
            counters["cache_hits"] += int(outcome["cache_hit"])
            counters["tombstone_hits"] += int(outcome["tombstone_hit"])
            counters[str(outcome["disposition"])] += 1
            if outcome["disposition"] == TerminalDisposition.QUARANTINED:
                record_once(
                    "LLM_HALLUCINATION_QUARANTINE",
                    "HIGH",
                    {"event_hash": stable_hash(event_id), "attempt_id": outcome.get("attempt_id")},
                )

        state = forensics.reconciliation()
        spent = daily_spend(forensics, cycle_at)
        if spent >= daily_budget * thresholds.budget_warning_fraction:
            record_once(
                "LLM_COST_BUDGET_WARNING",
                "WARNING",
                {"spent_usd": spent, "daily_budget_usd": daily_budget},
            )
        if state["transport_health"] == "UNAVAILABLE":
            record_once(
                "LLM_PROVIDER_DOWN", "HIGH", {"transport_health": state["transport_health"]}
            )
        if state["transport_health"] == "RATE_LIMITED":
            record_once(
                "LLM_RATE_LIMITED", "WARNING", {"transport_health": state["transport_health"]}
            )
        if state["semantic_health"] == "CRITICAL_FAILURE_RATE":
            record_once(
                "LLM_SCHEMA_FAILURE_SPIKE", "HIGH", {"semantic_health": state["semantic_health"]}
            )
        return {
            "status": "SUCCEEDED",
            **persisted,
            "duplicates": len(events) - persisted["records_new"],
            **counters,
        }

    worker = IntelligenceWorker(
        operations,
        {"rbi-rss": collect, "sebi-rss": collect},
        mode=IntelligenceRuntimeMode.INTERNAL_LIVE,
        job_timeout_seconds=180,
    )
    while datetime.now(UTC) < manifest.target_end_at:
        cycle_results = worker.run_once()
        try:
            fresh = build_manifest(
                config, now=manifest.started_at, model=model, soak_id=soak_id
            ).model_copy(update={"target_end_at": manifest.target_end_at})
            manifest.assert_frozen(fresh)
        except ValueError:
            qualifying = False
            record_once(
                "SOAK_CONFIGURATION_DRIFT",
                "CRITICAL",
                {"manifest_hash": manifest.soak_manifest_hash},
            )
        write_json(
            status_path,
            {
                "state": "RUNNING",
                "qualifying": qualifying,
                "process_id": os.getpid(),
                "started_at": manifest.started_at.isoformat(),
                "target_end_at": manifest.target_end_at.isoformat(),
                "last_heartbeat_at": datetime.now(UTC).isoformat(),
                "last_cycle_results": cycle_results,
                "counts": operations.counts(),
                "forensics": forensics.reconciliation(),
            },
        )
        time.sleep(5)

    ended_at = datetime.now(UTC)
    rows = operations.connection.execute(
        "SELECT job_name,status,result_json FROM executions ORDER BY scheduled_for"
    ).fetchall()
    results = [json.loads(row["result_json"] or "{}") for row in rows]
    collection = {
        "cycles": len(rows),
        "records_seen": sum(int(row.get("records_seen", 0)) for row in results),
        "canonical_events": operations.counts()["information_events"],
        "duplicates_suppressed": sum(int(row.get("duplicates", 0)) for row in results),
        "source_failures": sum(
            row["status"] != "SUCCEEDED"
            for row in rows
            if row["job_name"] in {"rbi-rss", "sebi-rss"}
        ),
    }
    entity_counts: Counter[str] = Counter()
    for event in operations.events():
        explicit = bool(re.search(r"\b(LIMITED|LTD|BANK|MATTER OF)\b", event.title.upper()))
        entity_counts[
            "EXPLICIT_ENTITY_NOT_RESOLVED" if explicit else "CORRECTLY_NON_COMPANY_SPECIFIC"
        ] += 1
    report: dict[str, Any] = {
        "label": "24H INTERNAL LIVE INTELLIGENCE SOAK — NOT A MARKET PREDICTION",
        "qualifying": qualifying,
        "manifest": manifest.model_dump(mode="json"),
        "ended_at": ended_at.isoformat(),
        "wall_clock_seconds": (ended_at - manifest.started_at).total_seconds(),
        "full_content_state": {
            key: full_content_access_state(
                retention_status=value.retention_status, notes=value.notes
            )
            for key, value in sources.items()
        },
        "collection": collection,
        "forensics": forensics.reconciliation(),
        "incidents": operations.incidents(),
        "entity_resolution": dict(entity_counts),
        "specialists": {
            "news_event": "LIVE",
            "macro": "PARTIALLY_LIVE",
            "psychology": "INSUFFICIENT",
            "fundamental": "ENGINEERING_ONLY",
            "technical": "ENGINEERING_ONLY",
            "historical": "ENGINEERING_ONLY",
            "flow_derivatives": "INSUFFICIENT",
        },
        "snapshots": {"generated": 0, "failures": 0},
        "fusion": {"state": "ABSTAIN", "mode": "PARTIAL_LIVE", "attempts": 0, "abstentions": 0},
        "research_mode": "ENGINEERING_FIXTURE",
    }
    report_dir = workspace / "research/intelligence"
    report_json, report_md = (
        report_dir / f"{soak_id}-report.json",
        report_dir / f"{soak_id}-report.md",
    )
    write_json(report_json, report)
    report_md.write_text(
        "# 24-Hour Live Intelligence Soak Report\n\n"
        + f"- Soak: {soak_id}\n- Started: {manifest.started_at.isoformat()}\n- Ended: {ended_at.isoformat()}\n- Qualifying: {qualifying}\n- Attempts: {report['forensics']['attempts']}\n- Cost: ${report['forensics']['cost_total_usd']:.10f}\n- Fusion: ABSTAIN / PARTIAL_LIVE\n- Research mode: ENGINEERING_FIXTURE\n",
        encoding="utf-8",
    )
    write_json(
        status_path,
        {
            "state": "COMPLETED",
            "qualifying": qualifying,
            "ended_at": ended_at.isoformat(),
            "report": str(report_json),
        },
    )
    forensics.close()
    operations.close()


if __name__ == "__main__":
    main()
