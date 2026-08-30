from datetime import UTC, datetime, timedelta

import pytest
from intelligence_core.entities import Entity, EntityResolver
from intelligence_core.fixtures import demo_entity, demo_timeline
from intelligence_core.processing import (
    CircuitBreaker,
    append_correction,
    cluster_events,
    novelty,
    source_health,
)
from intelligence_core.snapshot import build_intelligence_snapshot


def test_entity_resolution_uses_anchors_and_preserves_ambiguity():
    entity = demo_entity()
    resolver = EntityResolver([entity])
    assert resolver.resolve("Reliance", isin="INE-DEMO-001").status == "MATCHED"
    assert resolver.resolve("DEMO_RELIANCE", symbol="DEMO_RELIANCE").confidence == 1
    assert resolver.resolve("unrelated company").status == "UNMATCHED"
    second = Entity("OTHER", "Other", None, (), ("Demo Reliance",))
    assert EntityResolver([entity, second]).resolve("Demo Reliance").status == "MULTI_ENTITY"


def test_duplicate_stories_form_one_cluster_without_multiplied_weight():
    events = demo_timeline()
    clusters = cluster_events(events)
    contract_clusters = [
        items for items in clusters.values() if any(e.event_type == "CONTRACT" for e in items)
    ]
    assert len(contract_clusters) == 1 and len(contract_clusters[0]) == 3
    assert novelty(contract_clusters[0][0], contract_clusters[0][:1]).state == "NEW"
    assert novelty(contract_clusters[0][-1], contract_clusters[0]).state in {
        "DUPLICATE",
        "FOLLOW_UP",
    }


def test_timeline_reconstruction_at_requested_cutoffs():
    events = demo_timeline()
    day = datetime(2026, 8, 28, tzinfo=UTC)
    expected = {(10, 0): 1, (10, 25): 2, (10, 30): 3, (14, 0): 5, (15, 30): 5, (17, 0): 6}
    for (hour, minute), count in expected.items():
        snapshot = build_intelligence_snapshot(
            "DEMO_RELIANCE", day.replace(hour=hour, minute=minute), events
        )
        assert len(snapshot.events) == count and len(snapshot.snapshot_hash) == 64
    preclose = build_intelligence_snapshot("DEMO_RELIANCE", day.replace(hour=15, minute=30), events)
    assert not any(event.event_type == "EARNINGS" for event in preclose.events)


def test_snapshot_abstains_when_intelligence_is_absent():
    snapshot = build_intelligence_snapshot(
        "UNKNOWN", datetime(2020, 1, 1, tzinfo=UTC), demo_timeline()
    )
    assert snapshot.abstention == "INSUFFICIENT_INTELLIGENCE"


def test_correction_chain_is_append_only_and_causal():
    initial = demo_timeline()[1]
    correction = initial.model_copy(
        update={
            "event_id": __import__("uuid").uuid4(),
            "source_event_id": "filing-corrected",
            "correction_of": initial.event_id,
            "published_at": initial.published_at + timedelta(hours=2),
            "observed_at": initial.observed_at + timedelta(hours=2),
            "available_at": initial.available_at + timedelta(hours=2),
            "title": "Corrected material contract",
        }
    )
    history = append_correction([initial], correction)
    assert history[0].title != history[1].title and len(history) == 2
    with pytest.raises(ValueError):
        append_correction([], correction)


def test_circuit_breaker_health_and_recovery():
    breaker = CircuitBreaker(2)
    assert breaker.health == "HEALTHY"
    breaker.record_failure()
    assert breaker.health == "DEGRADED"
    breaker.record_failure()
    assert breaker.opened and breaker.health == "FAILING"
    breaker.record_success()
    assert breaker.health == "HEALTHY"


def test_source_health_states():
    now = datetime.now(UTC)
    assert (
        source_health(
            last_success=now,
            now=now,
            expected_freshness=timedelta(hours=1),
            failure_rate=0,
            schema_failures=0,
        )
        == "HEALTHY"
    )
    assert (
        source_health(
            last_success=now - timedelta(days=1),
            now=now,
            expected_freshness=timedelta(hours=1),
            failure_rate=0,
            schema_failures=0,
        )
        == "STALE"
    )
    assert (
        source_health(
            last_success=None,
            now=now,
            expected_freshness=timedelta(hours=1),
            failure_rate=0,
            schema_failures=0,
        )
        == "UNKNOWN"
    )
    assert (
        source_health(
            last_success=now,
            now=now,
            expected_freshness=timedelta(hours=1),
            failure_rate=0.6,
            schema_failures=0,
        )
        == "FAILING"
    )
    assert (
        source_health(
            last_success=now,
            now=now,
            expected_freshness=timedelta(hours=1),
            failure_rate=0,
            schema_failures=0,
            disabled=True,
        )
        == "DISABLED"
    )
