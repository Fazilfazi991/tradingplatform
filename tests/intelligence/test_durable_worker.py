import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.durable import DurableJob, SQLiteOperationsStore, next_run_at
from intelligence_core.live import collect_and_persist, live_source_handlers, operational_handlers
from intelligence_core.models import (
    CollectionPolicy,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)
from intelligence_core.semantic_runtime import configured_semantic_handler
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
    worker = IntelligenceWorker(
        store,
        {"poll": lambda _job, _now: {"status": "OK"}},
        mode=IntelligenceRuntimeMode.FIXTURE,
    )
    worker.run_once(now=start + timedelta(hours=2))
    assert store.incidents()[0]["incident_type"] == "SCHEDULER_MISSED_RUN"
    worker.request_shutdown()
    assert worker.shutdown.is_set()


def test_missing_handler_fails_closed_and_records_incident(tmp_path):
    now = datetime(2026, 8, 30, tzinfo=UTC)
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    store.load_config(config(tmp_path), now=now)
    with pytest.raises(ValueError, match="missing required job handlers: poll"):
        IntelligenceWorker(store, {}, mode=IntelligenceRuntimeMode.FIXTURE)
    assert store.incidents()[0]["incident_type"] == "SCHEDULER_HANDLER_MISSING"


def test_handler_failure_is_sanitized_and_incidented(tmp_path):
    now = datetime(2026, 8, 30, tzinfo=UTC)
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    store.load_config(config(tmp_path), now=now)

    def broken(_job, _now):
        raise RuntimeError("sensitive provider body")

    worker = IntelligenceWorker(
        store, {"poll": broken}, mode=IntelligenceRuntimeMode.FIXTURE
    )
    result = worker.run_once(now=now + timedelta(minutes=15))[0]
    assert result == {"job": "poll", "status": "FAILED", "error": "RuntimeError"}
    incident = store.incidents()[0]
    assert incident["incident_type"] == "SOURCE_COLLECTION_FAILURE"
    assert "sensitive provider body" not in json.dumps(incident)


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
    assert restarted.counts()["checkpoints"] == 1
    assert restarted.checkpoint(source.source_id) == collector.checkpoint()


def test_collection_retries_are_bounded_and_checkpoint_advances(tmp_path):
    attempts = 0

    def flaky(request):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ConnectError("temporary", request=request)
        return httpx.Response(200, content=b"<rss><channel/></rss>", headers={"content-type": "text/xml"})

    source = initial_sources()[0]
    item = OfficialRssCollector(
        source,
        CollectionPolicy(
            source_id=source.source_id,
            cadence_seconds=900,
            retries=2,
            backoff_seconds=0,
        ),
        "https://rbi.org.in/feed.xml",
        transport=httpx.MockTransport(flaky),
    )
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    result = collect_and_persist(store, item, sleeper=lambda _seconds: None)
    assert result["retries"] == 2 and attempts == 3
    assert store.checkpoint(source.source_id) == item.checkpoint()


def test_every_configured_job_has_an_operational_handler(tmp_path):
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    names = set(live_source_handlers(store)) | set(operational_handlers(store, tmp_path / "out"))
    names.add("llm-event-analysis")
    configured = json.loads(Path("config/intelligence-schedules.json").read_text())
    assert names == {job["name"] for job in configured["jobs"]}


def test_source_health_incident_is_deduplicated_and_resolvable(tmp_path):
    now = datetime(2026, 8, 30, 12, tzinfo=UTC)
    store = SQLiteOperationsStore(tmp_path / "ops.db")
    health = operational_handlers(store, tmp_path / "out")["source-health"]
    job = DurableJob("source-health", "INTERVAL", None, 3600, None, None, now, "1")
    first = health(job, now)
    assert first["source_health"]
    opened = len(store.incidents())
    health(job, now + timedelta(minutes=5))
    assert len(store.incidents()) == opened

    xml = b"""<rss><channel><item><title>Update</title><link>https://rbi.org.in/a</link>
    <guid>fresh-1</guid><pubDate>Sun, 30 Aug 2026 12:00:00 +0000</pubDate></item></channel></rss>"""
    source = initial_sources()[0]
    item = OfficialRssCollector(
        source,
        CollectionPolicy(source_id=source.source_id, cadence_seconds=900),
        "https://rbi.org.in/feed.xml",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, content=xml, headers={"content-type": "text/xml"}
            )
        ),
    )
    collect_and_persist(store, item)
    health(job, now + timedelta(minutes=10))
    rbi_incidents = [
        incident for incident in store.incidents() if incident.get("source_id") == source.source_id
    ]
    assert rbi_incidents[0]["status"] == "RESOLVED"


def test_semantic_runtime_is_safely_disabled_without_explicit_activation(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("LLM_RUNTIME_ENABLED", raising=False)
    handler = configured_semantic_handler(
        SQLiteOperationsStore(tmp_path / "ops.db"), workspace=Path.cwd()
    )
    now = datetime(2026, 8, 30, tzinfo=UTC)
    job = DurableJob("llm-event-analysis", "INTERVAL", None, 3600, None, None, now, "1")
    assert handler(job, now) == {
        "status": "DISABLED",
        "reason": "LLM_RUNTIME_ENABLED_FALSE",
        "prediction_state": "UNCHANGED",
    }
