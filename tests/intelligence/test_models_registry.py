import pytest
from intelligence_core.catalog import initial_sources
from intelligence_core.models import (
    AccessMethod,
    CollectionPolicy,
    HealthStatus,
    IntelligenceSource,
    ReliabilityTier,
    SourceCategory,
    SourceStatus,
)
from intelligence_core.registry import SourceCandidateRegistry, SourceRegistry
from pydantic import ValidationError


def source(*, active=True, status=SourceStatus.ACTIVE_FIXTURE):
    return IntelligenceSource(
        source_id="fixture",
        name="Fixture",
        source_category=SourceCategory.NEWS,
        provider="Verified Edge",
        base_url="https://fixtures.verified-edge.invalid",
        access_method=AccessMethod.FIXTURE,
        official_status=False,
        update_frequency="manual",
        expected_latency_seconds=0,
        license_status=status,
        rate_limit_policy="local only",
        reliability_tier=ReliabilityTier.TIER_1_PRIMARY,
        active=active,
    )


def test_source_registry_separates_reliability_and_predictive_value():
    registry = SourceRegistry()
    item = source()
    registry.register(item)
    assert registry.get("fixture").reliability_tier == ReliabilityTier.TIER_1_PRIMARY
    assert registry.get("fixture").predictive_status == "UNKNOWN"
    registry.update_health("fixture", HealthStatus.HEALTHY)
    assert registry.get("fixture").health_status == HealthStatus.HEALTHY
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(item)


def test_unapproved_source_cannot_activate():
    registry = SourceRegistry()
    with pytest.raises(ValueError, match="approved"):
        registry.register(source(status=SourceStatus.REVIEW_REQUIRED))


def test_collection_policy_enforces_conservative_cadence():
    assert CollectionPolicy(source_id="x", cadence_seconds=900).maximum_requests == 1
    with pytest.raises(ValidationError):
        CollectionPolicy(source_id="x", cadence_seconds=30)
    with pytest.raises(ValidationError):
        CollectionPolicy(source_id="x", cadence_seconds=900, maximum_requests=30)


def test_source_candidate_requires_human_review():
    registry = SourceCandidateRegistry()
    record = {"candidate_id": "c1", "name": "Candidate", "review_status": "ACTIVE"}
    with pytest.raises(ValueError, match="activate"):
        registry.propose(record)
    record["review_status"] = "NEW"
    registry.propose(record)
    assert registry.get("c1")["review_status"] == "PROPOSED"
    registry.review("c1", decision="REVIEW_REQUIRED", reason="terms unclear")
    assert registry.get("c1")["decision"] == "REVIEW_REQUIRED"


def test_event_time_contract_rejects_prepublication_availability():
    from intelligence_core.fixtures import demo_timeline

    event = demo_timeline()[0]
    with pytest.raises(ValidationError, match="publication"):
        event.model_copy(
            update={"available_at": event.published_at.replace(year=2025)}
        ).model_validate(
            event.model_dump() | {"available_at": event.published_at.replace(year=2025)}
        )


def test_initial_official_sources_are_narrow_internal_rss_only():
    sources = initial_sources()
    assert {source.source_id for source in sources} == {"rbi-press-releases-rss", "sebi-rss"}
    assert all(
        source.active and source.access_method == AccessMethod.OFFICIAL_RSS for source in sources
    )
    assert all(source.predictive_status == "UNKNOWN" for source in sources)
