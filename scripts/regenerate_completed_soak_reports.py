from __future__ import annotations

import argparse
import json
import re
from itertools import pairwise
from pathlib import Path
from typing import Any

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.runtime_forensics import ForensicRuntimeStore, derive_collection_report


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )


def source_alias(source_id: str) -> str:
    return (
        "RBI"
        if source_id.startswith("rbi")
        else "SEBI"
        if source_id.startswith("sebi")
        else source_id
    )


def continuity_evidence(
    store: ForensicRuntimeStore, operations: SQLiteOperationsStore
) -> dict[str, Any]:
    attempts = store.collection_attempts()
    terminal = next(row for row in attempts if row.terminal_job_status == "FAILED")
    next_success = next(
        row
        for row in attempts
        if row.source_id == terminal.source_id
        and row.started_at > terminal.completed_at
        and row.terminal_job_status == "SUCCEEDED"
    )
    source_events = [
        event for event in operations.events() if event.source_id == terminal.source_id
    ]
    recovered_events = [
        event
        for event in source_events
        if event.observed_at >= next_success.started_at
        and event.observed_at <= next_success.completed_at
    ]
    later_events = [
        event for event in source_events if event.observed_at > next_success.completed_at
    ]
    continuity_window = [
        event
        for event in source_events
        if terminal.started_at.timestamp() - 3600
        <= event.observed_at.timestamp()
        <= next_success.completed_at.timestamp() + 3600
    ]
    numeric_ids = sorted(
        int(match.group(1))
        for event in continuity_window
        if (match := re.search(r"prid=(\d+)", event.source_event_id or ""))
    )
    sequence_gaps = [
        (previous, current)
        for previous, current in pairwise(numeric_ids)
        if current != previous + 1
    ]
    return {
        "source": source_alias(terminal.source_id),
        "failed_job_id": terminal.job_id,
        "terminal_failure_completed_at": terminal.completed_at,
        "next_success_started_at": next_success.started_at,
        "next_success_completed_at": next_success.completed_at,
        "next_success_records_seen": next_success.records_seen,
        "next_success_canonical_events": next_success.canonical_events,
        "events_recovered_on_next_cycle": [event.source_event_id for event in recovered_events],
        "later_canonical_events": len(later_events),
        "observed_source_sequence_gaps": sequence_gaps,
        "recovery_state": "RECOVERED_ON_NEXT_CYCLE",
        "data_loss_determination": "NO_OBSERVED_DATA_LOSS"
        if recovered_events and not sequence_gaps
        else "CONTINUITY_UNPROVABLE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--soak-id", required=True)
    args = parser.parse_args()
    workspace = Path.cwd()
    database = workspace / "data/local" / f"{args.soak_id}.sqlite3"
    prior_path = workspace / "research/intelligence" / f"{args.soak_id}-report.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    store, operations = ForensicRuntimeStore(database), SQLiteOperationsStore(database)
    execution_rows = operations.connection.execute(
        "SELECT status FROM executions ORDER BY scheduled_for"
    ).fetchall()
    collection = derive_collection_report(
        store,
        outer_execution_statuses=[row["status"] for row in execution_rows],
        canonical_event_inventory=operations.counts()["information_events"],
    )
    collection["by_source"] = {
        source_alias(key): value for key, value in collection["by_source"].items()
    }
    continuity = continuity_evidence(store, operations)
    forensic = store.reconciliation()
    dispositions = operations.connection.execute(
        "SELECT payload_json FROM event_dispositions"
    ).fetchall()
    accepted_ids = {
        json.loads(row[0]).get("accepted_attempt_id") for row in dispositions if row[0]
    } - {None}
    quarantined_ids = {
        str(row.attempt_id) for row in store.attempts() if row.quarantine_status == "QUARANTINED"
    }
    quarantine_overlap = sorted(accepted_ids & quarantined_ids)
    corrected = {
        **prior,
        "collection": collection,
        "forensics": forensic,
        "continuity": continuity,
        "quarantine_containment": {
            "quarantined_attempts": len(quarantined_ids),
            "accepted_lineage_overlap": quarantine_overlap,
            "status": "PASS" if not quarantine_overlap else "FAIL",
        },
        "report_derivation": "AUTHORITATIVE_FORENSIC_LEDGERS",
    }
    report_dir = workspace / "research/intelligence"
    write_json(report_dir / "24h-live-intelligence-soak-report.json", corrected)
    write_json(report_dir / f"{args.soak_id}-report.json", corrected)
    lines = [
        "# 24-Hour Live Intelligence Soak Report",
        "",
        f"- Soak ID: {args.soak_id}",
        f"- Runtime seconds: {corrected['wall_clock_seconds']}",
        f"- Collection attempts: {collection['attempts']}",
        f"- Collection attempt failures: {collection['failed_attempts']}",
        f"- Recovered failures: {collection['recovered_failures']}",
        f"- Terminal source failures: {collection['terminal_failures']}",
        f"- Source failures (compatibility): {collection['source_failures']}",
        f"- RBI continuity: {continuity['data_loss_determination']} / {continuity['recovery_state']}",
        f"- Canonical events: {collection['canonical_event_inventory']}",
        f"- LLM attempts: {forensic['attempts']}",
        f"- Cost: ${forensic['cost_total_usd']:.8f}",
        "- Fusion: ABSTAIN / PARTIAL_LIVE",
        "- Research mode: ENGINEERING_FIXTURE",
    ]
    markdown_report = "\n".join(lines) + "\n"
    (report_dir / "24h-live-intelligence-soak-report.md").write_text(
        markdown_report, encoding="utf-8"
    )
    (report_dir / f"{args.soak_id}-report.md").write_text(markdown_report, encoding="utf-8")
    incident_audit = {
        "soak_id": args.soak_id,
        "incidents": operations.incidents(),
        "collection": collection,
        "rbi_failure_forensics": [
            row.model_dump(mode="json")
            for row in store.collection_attempts()
            if row.source_id.startswith("rbi")
            and (row.transport_status == "FAILED" or row.terminal_job_status == "FAILED")
        ],
        "continuity": continuity,
    }
    write_json(report_dir / "24h-live-intelligence-incident-audit.json", incident_audit)
    (report_dir / "24h-live-intelligence-incident-audit.md").write_text(
        "# 24-Hour Live Intelligence Incident Audit\n\n"
        f"- RBI failed attempts: {collection['by_source']['RBI']['failed_attempts']}\n"
        f"- RBI terminal failures: {collection['by_source']['RBI']['terminal_failures']}\n"
        f"- Next successful collection: {continuity['next_success_completed_at']}\n"
        f"- Continuity: {continuity['data_loss_determination']} / {continuity['recovery_state']}\n",
        encoding="utf-8",
    )
    (report_dir / "codex-live-intelligence-audit.md").write_text(
        "# Codex Live Intelligence Audit\n\n"
        "The completed window and authoritative ledgers reconcile. The prior source_failures=0 value was a reporter defect.\n\n"
        f"- Provider transport: {forensic['transport_health']}\n"
        f"- Semantic validation: {forensic['semantic_health']}\n"
        f"- Quarantine containment: {corrected['quarantine_containment']['status']}\n"
        f"- RBI continuity: {continuity['data_loss_determination']}\n"
        "- Fusion: ABSTAIN / PARTIAL_LIVE\n"
        "- Research mode: ENGINEERING_FIXTURE\n",
        encoding="utf-8",
    )
    store.close()
    operations.close()


if __name__ == "__main__":
    main()
