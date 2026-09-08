from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from research_core.common import stable_hash

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.runtime_forensics import (
    ForensicRuntimeStore,
    semantic_health,
    transport_health,
)


def _latest_execution(
    store: SQLiteOperationsStore, job_name: str, *, successful_only: bool = False
) -> dict[str, Any] | None:
    status_clause = "AND status='SUCCEEDED'" if successful_only else ""
    row = store.connection.execute(
        "SELECT scheduled_for,started_at,ended_at,status,result_json FROM executions "
        f"WHERE job_name=? {status_clause} ORDER BY started_at DESC LIMIT 1",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {
        "scheduled_for": row["scheduled_for"],
        "started_at": row["started_at"],
        "completed_at": row["ended_at"],
        "status": row["status"],
        "result": json.loads(row["result_json"] or "{}"),
    }


def build_current_health(
    store: SQLiteOperationsStore,
    forensics: ForensicRuntimeStore,
    *,
    schedules: dict[str, Any],
    policy: dict[str, Any],
    now: datetime,
    runtime_lock: dict[str, Any] | None = None,
    expected_policy_identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    now = now.astimezone(UTC)
    heartbeat_limit = timedelta(seconds=int(policy["heartbeat_stale_seconds"]))
    worker = store.service_status(now=now, stale_after=heartbeat_limit)
    source_jobs = {
        job["source_id"]: job
        for job in schedules["jobs"]
        if job.get("source_id") in {"rbi-press-releases-rss", "sebi-rss"}
    }
    sources: dict[str, Any] = {}
    for source_id, definition in source_jobs.items():
        execution = _latest_execution(store, definition["name"])
        success = _latest_execution(store, definition["name"], successful_only=True)
        threshold = int(definition["cadence_seconds"]) * int(
            policy["source_freshness_cadence_multiplier"]
        )
        completed = (
            datetime.fromisoformat(success["completed_at"])
            if success and success["completed_at"]
            else None
        )
        age = (now - completed.astimezone(UTC)).total_seconds() if completed else None
        sources[source_id] = {
            "state": "CURRENT" if age is not None and age <= threshold else "STALE",
            "last_success_at": completed.isoformat() if completed else None,
            "age_seconds": round(age, 3) if age is not None else None,
            "freshness_threshold_seconds": threshold,
            "freshness_basis": "configured_cadence_x_multiplier",
            "latest_execution": execution,
        }

    started_at = worker.get("started_at")
    attempts = [
        row
        for row in forensics.attempts()
        if row.completed_at >= now - timedelta(seconds=int(policy["semantic_health_window_seconds"]))
    ]
    latest_attempt = max(attempts, key=lambda row: row.completed_at) if attempts else None
    latest_policy_identity = (
        {
            "provider": latest_attempt.provider,
            "model": latest_attempt.model,
            "prompt_version": latest_attempt.prompt_version,
            "schema_version": latest_attempt.schema_version,
            "schema_hash": latest_attempt.schema_hash,
            "routing_version": latest_attempt.routing_version,
            "configuration_hash": latest_attempt.configuration_hash,
            "retry_policy_version": latest_attempt.retry_policy_version,
            "grounding_policy_version": latest_attempt.grounding_policy_version,
        }
        if latest_attempt
        else None
    )
    policy_identity = expected_policy_identity or latest_policy_identity
    current_policy_attempts = (
        [
            row
            for row in attempts
            if all(getattr(row, field) == value for field, value in policy_identity.items())
        ]
        if policy_identity
        else []
    )
    current_operational_attempts = [
        row
        for row in current_policy_attempts
        if not row.canonical_event_id.startswith("CANARY:")
    ]
    collection_attempts = forensics.collection_attempts()
    if started_at:
        start = datetime.fromisoformat(started_at)
        collection_attempts = [row for row in collection_attempts if row.completed_at >= start]
    observation: dict[str, Any] = {}
    minimum_cycles = int(policy["minimum_recovery_cycles"])
    late_tolerance = float(policy["scheduler_late_tolerance_seconds"])
    for source_id in source_jobs:
        selected = [row for row in collection_attempts if row.source_id == source_id]
        successful = [row for row in selected if row.terminal_job_status == "SUCCEEDED"]
        delays = [(row.started_at - row.scheduled_for).total_seconds() for row in selected]
        observation[source_id] = {
            "required_cycles": minimum_cycles,
            "executed_cycles": len({row.job_id for row in selected}),
            "successful_cycles": len({row.job_id for row in successful}),
            "failed_attempts": sum(row.transport_status.value == "FAILED" for row in selected),
            "recovered_failures": sum(row.recovered for row in selected),
            "late_cycles": sum(delay > late_tolerance for delay in delays),
            "late_tolerance_seconds": late_tolerance,
            "max_scheduling_delay_seconds": round(max(delays, default=0.0), 3),
        }
    observation_complete = all(
        value["successful_cycles"] >= minimum_cycles and value["late_cycles"] == 0
        for value in observation.values()
    )
    transport = transport_health(attempts).value
    semantic_minimum = int(policy["semantic_policy_minimum_attempts"])
    semantic_window_complete = len(current_operational_attempts) >= semantic_minimum
    semantic = (
        semantic_health(
            current_operational_attempts,
            elevated=float(policy["semantic_elevated_failure_rate"]),
            critical=float(policy["semantic_critical_failure_rate"]),
        ).value
        if semantic_window_complete
        else "INSUFFICIENT_SAMPLE"
    )
    quarantined_attempts = sum(
        row.quarantine_status == "QUARANTINED" for row in current_operational_attempts
    )
    latest_by_event = {}
    for row in current_operational_attempts:
        latest_by_event[row.canonical_event_id] = row
    terminal_quarantines = sum(
        row.terminal_disposition.value == "QUARANTINED" for row in latest_by_event.values()
    )
    validation_failures = [
        row
        for row in current_operational_attempts
        if row.structured_validation_status.value == "FAIL"
    ]
    transport_failures = [
        row for row in current_operational_attempts if row.transport_status.value == "FAILED"
    ]
    collection_failures = [
        row for row in collection_attempts if row.transport_status.value == "FAILED"
    ]
    input_tokens = sum(row.input_tokens for row in attempts)
    output_tokens = sum(row.output_tokens for row in attempts)
    cost = sum(row.estimated_total_cost for row in attempts)
    open_incidents = [
        row for row in store.incidents() if row.get("status") in {"OPEN", "ACKNOWLEDGED"}
    ]
    alerts: list[str] = []
    if any(value["late_cycles"] for value in observation.values()):
        alerts.append("SCHEDULER_LATE_CYCLE")
    if worker["status"] != "RUNNING":
        alerts.append("WORKER_NOT_RUNNING" if worker["status"] != "NOT_STARTED" else "WORKER_NOT_STARTED")
    for source_id, source in sources.items():
        if source["state"] != "CURRENT":
            alerts.append("RBI_STALE" if source_id.startswith("rbi") else "SEBI_STALE")
    if transport not in {"HEALTHY", "UNKNOWN"}:
        alerts.append("PROVIDER_TRANSPORT_DEGRADED")
    if semantic in {"ELEVATED_FAILURES", "CRITICAL_FAILURE_RATE"}:
        alerts.append("SEMANTIC_FAILURE_SPIKE")
    if not semantic_window_complete:
        alerts.append("SEMANTIC_SAMPLE_INCOMPLETE")
    if terminal_quarantines >= int(policy["quarantine_warning_count"]):
        alerts.append("QUARANTINE_SPIKE")
    alerts.extend(
        sorted(
            {
                str(row["incident_type"])
                for row in open_incidents
                if row["incident_type"]
                in {
                    "SOURCE_COLLECTION_FAILURE",
                    "LLM_PROVIDER_DOWN",
                    "LLM_RATE_LIMITED",
                    "LLM_SCHEMA_FAILURE_SPIKE",
                    "LLM_COST_BUDGET_WARNING",
                    "LLM_COST_BUDGET_EXCEEDED",
                    "LLM_HALLUCINATION_QUARANTINE",
                    "SCHEDULER_MISSED_RUN",
                }
            }
        )
    )
    alerts = sorted(set(alerts))
    drift: dict[str, dict[str, str]] = {}
    if runtime_lock:
        for name, expected in runtime_lock["files"].items():
            actual = sha256(Path(name).read_bytes()).hexdigest() if Path(name).is_file() else "ABSENT"
            if actual != expected:
                drift[name] = {"expected": expected, "actual": actual}
    if drift:
        alerts.append("CONFIGURATION_DRIFT")
    scheduler_state = "ACTIVE" if worker["status"] == "RUNNING" else "INACTIVE"
    source_current = all(row["state"] == "CURRENT" for row in sources.values())
    overall = (
        "HEALTHY"
        if worker["status"] == "RUNNING"
        and scheduler_state == "ACTIVE"
        and source_current
        and transport == "HEALTHY"
        and semantic == "HEALTHY"
        and not alerts
        and observation_complete
        else "DEGRADED"
    )
    return {
        "version": policy["version"],
        "generated_at": now.isoformat(),
        "overall_state": overall,
        "runtime_mode": "INTERNAL_LIVE",
        "public_delivery": "BLOCKED",
        "forward_paper": "DISABLED",
        "worker": worker,
        "scheduler": {"state": scheduler_state, "configuration_version": schedules["version"]},
        "sources": sources,
        "scheduled_observation": {
            "complete": observation_complete,
            "sources": observation,
        },
        "provider_transport_health": transport,
        "semantic_validation_health": semantic,
        "llm": {
            "provider": "openai",
            "model": attempts[-1].model if attempts else "gpt-5.6-luna",
            "attempts": len(attempts),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(cost, 8),
            "quarantines": terminal_quarantines,
            "quarantined_attempts": quarantined_attempts,
            "transport_failures": len(transport_failures),
            "validation_failures": len(validation_failures),
            "current_policy": {
                "identity": policy_identity,
                "minimum_operational_attempts": semantic_minimum,
                "operational_attempts": len(current_operational_attempts),
                "canary_attempts": len(current_policy_attempts)
                - len(current_operational_attempts),
                "window_complete": semantic_window_complete,
                "transport_failures": len(transport_failures),
                "validation_failures": len(validation_failures),
                "failure_rate": round(
                    len(validation_failures) / len(current_operational_attempts), 6
                )
                if current_operational_attempts
                else None,
            },
            "historical_window_totals": {
                "attempts": len(attempts),
                "transport_failures": sum(
                    row.transport_status.value == "FAILED" for row in attempts
                ),
                "validation_failures": sum(
                    row.structured_validation_status.value == "FAIL" for row in attempts
                ),
            },
        },
        "cache": {
            "entries": int(
                forensics.connection.execute("SELECT COUNT(*) FROM semantic_success_cache").fetchone()[0]
            ),
            "active_tombstones": int(
                forensics.connection.execute(
                    "SELECT COUNT(*) FROM invalid_semantic_tombstones WHERE expires_at>?",
                    (now.isoformat(),),
                ).fetchone()[0]
            ),
        },
        "open_incidents": open_incidents,
        "recent_collection_failures": [
            {
                "attempt_id": str(row.attempt_id),
                "source_id": row.source_id,
                "error_class": row.error_class,
                "completed_at": row.completed_at.isoformat(),
                "terminal_job_status": row.terminal_job_status,
            }
            for row in collection_failures[-20:]
        ],
        "recent_llm_failures": [
            {
                "attempt_id": str(row.attempt_id),
                "transport_status": row.transport_status.value,
                "validation_category": (
                    row.validation_error_category.value if row.validation_error_category else None
                ),
                "completed_at": row.completed_at.isoformat(),
            }
            for row in (transport_failures + validation_failures)[-20:]
        ],
        "recent_quarantines": [
            {
                "attempt_id": str(row.attempt_id),
                "canonical_event_id": row.canonical_event_id,
                "validation_category": (
                    row.validation_error_category.value if row.validation_error_category else None
                ),
                "completed_at": row.completed_at.isoformat(),
            }
            for row in attempts
            if row.quarantine_status == "QUARANTINED"
        ][-20:],
        "alerts": alerts,
        "configuration_drift": {"state": "FAIL" if drift else "PASS", "mismatches": drift},
        "configuration_hash": stable_hash(
            {"schedules": schedules, "health_policy": policy, "sources": sorted(source_jobs)}
        ),
    }


def write_current_health(report: dict[str, Any], output_root: str | Path) -> tuple[Path, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "current-intelligence-health.json"
    md_path = root / "current-intelligence-health.md"
    json_tmp = json_path.with_suffix(".json.tmp")
    md_tmp = md_path.with_suffix(".md.tmp")
    json_tmp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_lines = [
        f"- {source_id}: {value['state']} (last success: {value['last_success_at']})"
        for source_id, value in report["sources"].items()
    ]
    md_tmp.write_text(
        "# Current Intelligence Health\n\n"
        f"Generated: {report['generated_at']}\n\n"
        f"Overall: **{report['overall_state']}**\n\n"
        f"Worker: {report['worker']['status']}\n\n"
        f"Scheduler: {report['scheduler']['state']}\n\n"
        + "## Sources\n\n"
        + "\n".join(source_lines)
        + "\n\n## LLM\n\n"
        + f"- Transport: {report['provider_transport_health']}\n"
        + f"- Semantic: {report['semantic_validation_health']}\n"
        + f"- Attempts: {report['llm']['attempts']}\n"
        + "- Current-policy operational sample: "
        + f"{report['llm']['current_policy']['operational_attempts']}/"
        + f"{report['llm']['current_policy']['minimum_operational_attempts']}\n"
        + f"- Current-policy canaries: {report['llm']['current_policy']['canary_attempts']}\n"
        + f"- Quarantines: {report['llm']['quarantines']}\n"
        + f"- Estimated cost: ${report['llm']['estimated_cost_usd']:.8f}\n\n"
        + "## Scheduled recovery observation\n\n"
        + f"Complete: {report['scheduled_observation']['complete']}\n\n"
        + "\n".join(
            f"- {source_id}: {value['successful_cycles']}/{value['required_cycles']} successful cycles"
            for source_id, value in report["scheduled_observation"]["sources"].items()
        )
        + "\n\n"
        + "Forward Paper remains **DISABLED**. Public delivery remains **BLOCKED**.\n",
        encoding="utf-8",
    )
    json_tmp.replace(json_path)
    md_tmp.replace(md_path)
    return json_path, md_path
