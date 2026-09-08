import json
from datetime import UTC, datetime, timedelta

from intelligence_core.current_health import build_current_health, write_current_health
from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.runtime_forensics import CollectionAttemptRecord, ForensicRuntimeStore

NOW = datetime(2026, 9, 8, 6, tzinfo=UTC)


def definitions():
    return {
        "version": "1",
        "timezone": "Asia/Kolkata",
        "jobs": [
            {
                "name": "rbi-rss",
                "kind": "INTERVAL",
                "source_id": "rbi-press-releases-rss",
                "cadence_seconds": 900,
            },
            {
                "name": "sebi-rss",
                "kind": "INTERVAL",
                "source_id": "sebi-rss",
                "cadence_seconds": 900,
            },
        ],
    }


def policy():
    return {
        "version": "v1",
        "heartbeat_stale_seconds": 30,
        "source_freshness_cadence_multiplier": 2,
        "scheduler_late_tolerance_seconds": 60,
        "semantic_elevated_failure_rate": 0.05,
        "semantic_critical_failure_rate": 0.2,
        "semantic_health_window_seconds": 86400,
        "quarantine_warning_count": 1,
        "minimum_recovery_cycles": 3,
    }


def test_current_health_reports_stale_without_worker(tmp_path):
    schedule_path = tmp_path / "schedules.json"
    schedule_path.write_text(json.dumps(definitions()), encoding="utf-8")
    store = SQLiteOperationsStore(tmp_path / "ops.sqlite3")
    store.load_config(schedule_path, now=NOW)
    forensics = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    report = build_current_health(
        store, forensics, schedules=definitions(), policy=policy(), now=NOW
    )
    assert report["overall_state"] == "DEGRADED"
    assert report["worker"]["status"] == "NOT_STARTED"
    assert report["alerts"] == ["RBI_STALE", "SEBI_STALE", "WORKER_NOT_STARTED"]


def test_current_health_uses_configured_cadence_and_writes_atomically(tmp_path):
    schedule_path = tmp_path / "schedules.json"
    schedule_path.write_text(json.dumps(definitions()), encoding="utf-8")
    store = SQLiteOperationsStore(tmp_path / "ops.sqlite3")
    store.load_config(schedule_path, now=NOW - timedelta(minutes=15))
    store.start_service("worker", 123, now=NOW - timedelta(seconds=5))
    for job in store.all_jobs():
        key = store.begin_execution(job, NOW - timedelta(minutes=1))
        assert key
        store.finish_execution(
            key,
            job,
            now=NOW - timedelta(minutes=1),
            status="SUCCEEDED",
            result={"records_seen": 1},
        )
    forensics = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    report = build_current_health(
        store, forensics, schedules=definitions(), policy=policy(), now=NOW
    )
    assert report["sources"]["sebi-rss"]["state"] == "CURRENT"
    assert report["sources"]["sebi-rss"]["freshness_threshold_seconds"] == 1800
    paths = write_current_health(report, tmp_path / "health")
    assert all(path.exists() for path in paths)
    assert not list((tmp_path / "health").glob("*.tmp"))


def test_current_health_detects_configuration_drift(tmp_path):
    schedule_path = tmp_path / "schedules.json"
    schedule_path.write_text(json.dumps(definitions()), encoding="utf-8")
    store = SQLiteOperationsStore(tmp_path / "ops.sqlite3")
    forensics = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    report = build_current_health(
        store,
        forensics,
        schedules=definitions(),
        policy=policy(),
        now=NOW,
        runtime_lock={"files": {str(schedule_path): "incorrect"}},
    )
    assert report["configuration_drift"]["state"] == "FAIL"
    assert "CONFIGURATION_DRIFT" in report["alerts"]


def test_recovery_observation_requires_three_on_time_cycles_per_source(tmp_path):
    store = SQLiteOperationsStore(tmp_path / "ops.sqlite3")
    forensics = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    for source_id in ("rbi-press-releases-rss", "sebi-rss"):
        for index in range(3):
            scheduled = NOW - timedelta(minutes=15 * (3 - index))
            forensics.add_collection_attempt(
                CollectionAttemptRecord(
                    job_id=f"{source_id}:{index}",
                    source_id=source_id,
                    scheduled_for=scheduled,
                    started_at=scheduled + timedelta(seconds=2),
                    completed_at=scheduled + timedelta(seconds=3),
                    attempt_ordinal=1,
                    transport_status="SUCCEEDED",
                    handler_status="SUCCEEDED",
                    parse_status="PASS",
                    records_seen=1,
                    canonical_events=0,
                    duplicate_count=1,
                    terminal_job_status="SUCCEEDED",
                    latency_ms=1000,
                    provenance_hash=f"{source_id}-{index}",
                )
            )
    report = build_current_health(
        store, forensics, schedules=definitions(), policy=policy(), now=NOW
    )
    assert report["scheduled_observation"]["complete"] is True
    assert all(
        value["successful_cycles"] == 3
        for value in report["scheduled_observation"]["sources"].values()
    )
