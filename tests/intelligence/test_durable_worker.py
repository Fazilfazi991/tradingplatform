import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.durable import SQLiteOperationsStore, next_run_at
from intelligence_core.live import collect_and_persist, live_source_handlers, operational_handlers
from intelligence_core.models import (
    CollectionPolicy,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)
from intelligence_core.worker import IntelligenceWorker


def config(tmp_path, jobs=None):
    path = tmp_path / "schedules.json"
    path.write_text(
        json.dumps(
            {
                "version": "1",
                "timezone": "Asia/Kolkata",
                "jobs": jobs
                or [
                    {
                        "name": "poll",
                        "kind": "INTERVAL",
                        "source_id": "fixture",
                        "cadence_seconds": 900,
                    }
                ],
            }
        )
    )
    return path


def test_runtime_mode_blocks_customer_and_production():
    IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.INTERNAL_LIVE)
    with pytest.raises(PermissionError):
        IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.CUSTOMER_VISIBLE)
    with pytest.raises(PermissionError):
        IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.PRODUCTION_INTERNAL)


def test_persistent_schedule_restart_and_idempotent_execution(tmp_path):
    start = datetime(2026, 8, 30, 10, tzinfo=UTC)
    database = tmp_path / "ops.db"
    store = SQLiteOperationsStore(database)
    store.load_config(config(tmp_path), now=start)
    store.close()
    restarted = SQLiteOperationsStore(database)
    due = start + timedelta(minutes=15)
    calls = []
    worker = IntelligenceWorker(
        restarted,
        {"poll": lambda job, now: calls.append(job.name) or {"ok": True}},
        mode=IntelligenceRuntimeMode.INTERNAL_LIVE,
    )
    assert worker.run_once(now=due)[0]["status"] == "SUCCEEDED"
    assert worker.run_once(now=due) == [] and calls == ["poll"]
    restarted.close()


def test_locking_expiry_and_interrupted_recovery(tmp_path):
    now = datetime(2026, 8, 30, tzinfo=UTC)
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    store.load_config(config(tmp_path), now=now)
    job = store.all_jobs()[0]
    assert store.acquire(job.name, "one", now=now, ttl=timedelta(seconds=10))
    assert not store.acquire(job.name, "two", now=now, ttl=timedelta(seconds=10))
    assert store.acquire(
        job.name, "two", now=now + timedelta(seconds=11), ttl=timedelta(seconds=10)
    )
    key = store.begin_execution(job, now)
    assert key
    assert store.recover_interrupted(now + timedelta(minutes=1)) == 1


def test_missed_run_opens_incident_and_shutdown_is_graceful(tmp_path):
    start = datetime(2026, 8, 30, tzinfo=UTC)
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    store.load_config(config(tmp_path), now=start)
    worker = IntelligenceWorker(store, {}, mode=IntelligenceRuntimeMode.FIXTURE)
    worker.run_once(now=start + timedelta(hours=2))
    assert store.incidents()[0]["incident_type"] == "SCHEDULER_MISSED_RUN"
    worker.request_shutdown()
    assert worker.shutdown.is_set()


def test_timezone_and_calendar_boundaries():
    definition = {"kind": "DAILY", "local_time": "16:30"}
    before = datetime(2026, 12, 31, 9, tzinfo=UTC)
    result = next_run_at(definition, before)
    assert result.tzinfo == UTC and result.hour == 11 and result.minute == 0
    after = datetime(2026, 12, 31, 12, tzinfo=UTC)
    assert next_run_at(definition, after).year == 2027
    weekly = next_run_at({"kind": "WEEKLY", "weekday": 0, "local_time": "09:00"}, before)
    assert weekly.astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata")).weekday() == 0


def test_collected_events_survive_restart_and_deduplicate(tmp_path):
    xml = b"""<rss><channel><item><title>Policy update</title>
    <link>https://rbi.org.in/policy</link><guid>policy-1</guid>
    <pubDate>Sun, 30 Aug 2026 10:00:00 +0000</pubDate></item></channel></rss>"""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, content=xml, headers={"content-type": "text/xml"})
    )
    source = initial_sources()[0]
    collector = OfficialRssCollector(
        source,
        CollectionPolicy(source_id=source.source_id, cadence_seconds=900),
        "https://rbi.org.in/feed.xml",
        transport=transport,
    )
    database = tmp_path / "ops.db"
    store = SQLiteOperationsStore(database)
    assert collect_and_persist(store, collector)["records_new"] == 1
    store.close()
    restarted = SQLiteOperationsStore(database)
    assert collect_and_persist(restarted, collector)["records_new"] == 0
    assert restarted.counts()["raw_artifacts"] == 1
    assert restarted.counts()["information_events"] == 1


def test_every_configured_job_has_an_operational_handler(tmp_path):
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    names = set(live_source_handlers(store)) | set(operational_handlers(store, tmp_path / "out"))
    configured = json.loads(Path("config/intelligence-schedules.json").read_text())
    assert names == {job["name"] for job in configured["jobs"]}
