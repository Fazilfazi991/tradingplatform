from datetime import UTC, datetime

import httpx
import pytest
from intelligence_core.collectors import (
    CollectorError,
    OfficialRssCollector,
    SecurityPolicyError,
    validate_url,
)
from intelligence_core.models import (
    AccessMethod,
    CollectionMode,
    CollectionPolicy,
    IntelligenceSource,
    ReliabilityTier,
    SourceCategory,
    SourceStatus,
)
from intelligence_core.scheduler import CollectionRunner, LocalScheduler, ScheduledJob


def source():
    return IntelligenceSource(
        source_id="sebi-rss",
        name="SEBI RSS",
        source_category=SourceCategory.NEWS,
        provider="SEBI",
        base_url="https://www.sebi.gov.in",
        access_method=AccessMethod.OFFICIAL_RSS,
        official_status=True,
        update_frequency="15 minutes",
        expected_latency_seconds=900,
        license_status=SourceStatus.ACTIVE_INTERNAL,
        internal_research_status="PERMITTED_OFFICIAL_RSS",
        retention_status="RSS_METADATA",
        rate_limit_policy="minimum 15 minutes",
        reliability_tier=ReliabilityTier.TIER_1_PRIMARY,
        active=True,
    )


def rss_transport(payload: bytes, content_type="application/rss+xml", status=200):
    return httpx.MockTransport(
        lambda request: httpx.Response(
            status, content=payload, headers={"content-type": content_type}, request=request
        )
    )


def collector(payload: bytes, **kwargs):
    return OfficialRssCollector(
        source(),
        CollectionPolicy(
            source_id="sebi-rss",
            cadence_seconds=900,
            failure_threshold=2,
            maximum_bytes=kwargs.get("maximum_bytes", 2000000),
        ),
        "https://www.sebi.gov.in/sebirss.xml",
        transport=rss_transport(payload, kwargs.get("content_type", "application/rss+xml")),
    )


RSS = b"<rss><channel><item><guid>1</guid><title>SEBI circular</title><link>https://www.sebi.gov.in/a</link><description>Official update</description><pubDate>Fri, 28 Aug 2026 10:00:00 GMT</pubDate></item></channel></rss>"


def test_official_rss_fetch_parse_normalize_and_replay():
    item = collector(RSS)
    artifact = item.fetch(item.discover()[0])
    records = item.parse(artifact)
    events = item.normalize(records, artifact)
    assert len(events) == 1 and events[0].source_event_id == "1"
    assert item.replay(artifact)[0].raw_payload_hash == artifact.sha256
    assert item.health_check() and item.checkpoint() is None


def test_official_alias_hosts_must_be_explicitly_configured():
    approved = source().model_copy(
        update={"entities_supported": ("sebi.gov.in", "www.sebi.gov.in")}
    )
    payload = RSS.replace(b"https://www.sebi.gov.in/a", b"https://sebi.gov.in/a")
    item = OfficialRssCollector(
        approved,
        CollectionPolicy(source_id="sebi-rss", cadence_seconds=900),
        "https://www.sebi.gov.in/sebirss.xml",
        transport=rss_transport(payload),
    )
    assert len(item.replay(item.fetch(item.feed_url))) == 1


def test_sebi_date_only_rss_timestamp_is_supported():
    from intelligence_core.collectors import _rss_time

    parsed = _rss_time("28 Aug, 2026 +0530")
    assert parsed and parsed.astimezone(UTC).hour == 18


def test_naive_indian_regulator_rss_time_is_interpreted_as_ist():
    from intelligence_core.collectors import _rss_time

    parsed = _rss_time("Mon, 31 Aug 2026 19:00:00")
    assert parsed == datetime(2026, 8, 31, 13, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.sebi.gov.in/a",
        "https://evil.test/a",
        "https://user:pass@www.sebi.gov.in/a",
        "https://www.sebi.gov.in:444/a",
    ],
)
def test_ssrf_allowlist_rejects_unsafe_urls(url):
    with pytest.raises(SecurityPolicyError):
        validate_url(url, {"www.sebi.gov.in"})


def test_content_type_size_and_malformed_controls():
    with pytest.raises(CollectorError, match="content type"):
        collector(RSS, content_type="text/html").fetch("https://www.sebi.gov.in/sebirss.xml")
    with pytest.raises(CollectorError, match="bounded"):
        collector(RSS, maximum_bytes=10).fetch("https://www.sebi.gov.in/sebirss.xml")
    with pytest.raises(CollectorError, match="malformed"):
        collector(b"<rss>").parse(collector(b"<rss>").fetch("https://www.sebi.gov.in/sebirss.xml"))


def test_runner_is_idempotent_and_records_ledger():
    runner = CollectionRunner()
    item = collector(RSS)
    policy = item.policy
    first = runner.run(item, policy, mode=CollectionMode.FIXTURE, code_sha="abc")
    second = runner.run(item, policy, mode=CollectionMode.REPLAY, code_sha="abc")
    assert first.records_new == 1 and second.records_duplicate == 1
    assert len(runner.events) == 1 and len(runner.ledger) == 2


def test_failure_opens_circuit_and_stops_promotion():
    runner = CollectionRunner()
    item = collector(b"broken")
    policy = item.policy
    assert runner.run(item, policy, mode=CollectionMode.FIXTURE).status == "FAILED"
    assert runner.run(item, policy, mode=CollectionMode.FIXTURE).status == "CIRCUIT_OPENED"
    assert runner.run(item, policy, mode=CollectionMode.FIXTURE).status == "CIRCUIT_OPEN"
    assert len(runner.raw_artifacts) == 1 and len(runner.events) == 0
    runner.breakers["sebi-rss"].record_success()
    assert not runner.breakers["sebi-rss"].opened


def test_scheduler_supports_all_requested_modes():
    scheduler = LocalScheduler()
    for mode in ("CRON", "INTERVAL", "MARKET_SESSION", "EVENT", "MANUAL"):
        scheduler.register(ScheduledJob(mode, "fixture", mode, cadence_seconds=3600))
    assert len(scheduler.due(datetime.now(UTC))) == 5
    with pytest.raises(ValueError):
        scheduler.register(ScheduledJob("CRON", "fixture", "CRON"))
