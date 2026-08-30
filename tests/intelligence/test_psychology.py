from datetime import UTC, datetime, timedelta

import pytest
from intelligence_core.psychology import (
    PsychologyEvidenceEngine,
    SentimentDirection,
    SentimentObservation,
    SentimentType,
    aggregate_sentiment,
    attention_metrics,
    build_psychology_snapshot,
    classify_disagreement,
    classify_intensity,
    narrative_lifecycle,
    psychology_qa,
    sentiment_breadth,
)
from intelligence_core.psychology_fixtures import (
    null_psychology_fixture,
    psychology_fixture_cases,
)
from intelligence_core.psychology_sources import psychology_source_candidates

NOW = datetime(2026, 8, 30, 12, tzinfo=UTC)


def observation(direction="POSITIVE", cluster="c1", hours=0, **updates):
    published = NOW - timedelta(hours=hours)
    values = {
        "entity_id": "RELIANCE", "source_id": f"source-{cluster}", "source_type": "NEWS",
        "content_reference": f"ref-{cluster}", "event_id": f"event-{cluster}",
        "cluster_id": cluster, "sentiment_type": SentimentType.NEWS_SENTIMENT,
        "sentiment_direction": SentimentDirection(direction), "sentiment_strength": 0.8,
        "certainty": 0.8, "relevance": 1, "source_reliability": 0.8, "novelty": 1,
        "confirmation_state": "MULTI_SOURCE_CONFIRMED", "attention_weight": 1,
        "published_at": published, "source_available_at": published,
        "system_observed_at": published,
        "available_at": published, "analyzer": "DETERMINISTIC",
        "analyzer_version": "1", "evidence_refs": (f"evidence-{cluster}",),
    }
    values.update(updates)
    return SentimentObservation(**values)


def test_observation_requires_causal_timing_scope_and_evidence():
    assert observation().payload_hash
    with pytest.raises(ValueError, match="available_at"):
        observation(available_at=NOW + timedelta(minutes=1))
    with pytest.raises(ValueError, match="scope"):
        observation(entity_id=None)
    with pytest.raises(ValueError, match="evidence"):
        observation(evidence_refs=())


def test_duplicate_cluster_is_one_attention_vote_and_preserves_source_records():
    original = observation(cluster="wire")
    rewrites = [observation(cluster="wire", source_id=f"rewrite-{i}") for i in range(10)]
    metrics = attention_metrics([original, *rewrites], NOW)
    assert metrics.unique_clusters == 1
    assert metrics.mentions_1h == 1
    assert metrics.duplicate_suppression_rate == pytest.approx(10 / 11)


def test_attention_velocity_and_acceleration_use_independent_clusters():
    records = [observation(cluster=f"new-{i}", hours=1) for i in range(4)]
    records += [observation(cluster="prior", hours=8), observation(cluster="old", hours=14)]
    metrics = attention_metrics(records, NOW)
    assert metrics.attention_velocity > 0 and metrics.attention_acceleration > 0
    assert metrics.unique_sources == 6 and metrics.source_diversity == 1


def test_aggregation_uses_quality_novelty_confirmation_and_rumour_discount():
    confirmed = observation("NEGATIVE", cluster="official", source_reliability=1)
    rumours = [observation("STRONGLY_POSITIVE", cluster=f"rumour-{i}", is_rumour=True,
                           confirmation_state="RUMOUR", source_reliability=0.2) for i in range(3)]
    direction, score, disagreement = aggregate_sentiment([confirmed, *rumours])
    assert direction in {SentimentDirection.NEGATIVE, SentimentDirection.SLIGHTLY_NEGATIVE}
    assert score < 0 and disagreement > 0


def test_narrative_lifecycle_and_reversal_are_explicit():
    assert narrative_lifecycle(0.5, 0.3, 0.2) == "ACCELERATING"
    assert narrative_lifecycle(0.9, 0, 0.8) == "SATURATED"
    assert narrative_lifecycle(0.5, 0, 0.4, reversal=True) == "REVERSING"
    assert narrative_lifecycle(0.05, 0, 0) == "DORMANT"
    assert narrative_lifecycle(0.3, -0.2, 0.2) == "WEAKENING"


def test_multi_input_fear_euphoria_disagreement_crowding_and_speculation():
    records = [observation("STRONGLY_NEGATIVE", cluster=f"n{i}") for i in range(4)]
    snapshot = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
                                         observations=records)
    assert snapshot.fear_state in {"ELEVATED", "HIGH", "EXTREME"}
    assert snapshot.euphoria_state != "EXTREME"
    assert snapshot.crowding_state == "UNKNOWN"
    assert classify_disagreement(0.7, 3) == "EXTREME"
    assert classify_intensity(0.9, 1) == "UNKNOWN"


def test_point_in_time_snapshot_excludes_future_and_evidence_engine_abstains():
    future = observation(cluster="future", system_observed_at=NOW + timedelta(hours=2),
                         source_available_at=NOW + timedelta(hours=1),
                         available_at=NOW + timedelta(hours=2))
    snapshot = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
                                         observations=[observation(), future])
    assert len(snapshot.observations) == 1 and snapshot.snapshot_hash
    result = PsychologyEvidenceEngine().evaluate(snapshot, horizon="1D")
    assert result.status == "INSUFFICIENT_PSYCHOLOGY_EVIDENCE"
    assert result.directional_evidence_score is None
    assert "price probability" in result.explanation_payload["not"]


def test_disagreement_reduces_certainty_and_is_explainable():
    aligned = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
        observations=[observation("POSITIVE", cluster=f"p{i}") for i in range(4)])
    divided = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
        observations=[observation("POSITIVE", cluster="p"), observation("NEGATIVE", cluster="n"),
                      observation("POSITIVE", cluster="p2"), observation("NEGATIVE", cluster="n2")])
    assert divided.sentiment.certainty < aligned.sentiment.certainty
    assert divided.sentiment.disagreement in {"HIGH", "EXTREME"}


def test_entity_sector_market_scope_and_breadth_require_sufficient_evidence():
    entity = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
        observations=[observation(cluster="e1"), observation(cluster="e2")]).sentiment
    sector_records = [observation(cluster="s1", entity_id=None, sector_id="ENERGY"),
                      observation(cluster="s2", entity_id=None, sector_id="ENERGY")]
    sector = build_psychology_snapshot(NOW, scope="SECTOR", scope_id="ENERGY",
                                       observations=sector_records).sentiment
    market_records = [observation(cluster="m1", entity_id=None, market_id="INDIA"),
                      observation("NEGATIVE", cluster="m2", entity_id=None, market_id="INDIA")]
    market = build_psychology_snapshot(NOW, scope="MARKET", scope_id="INDIA",
                                       observations=market_records).sentiment
    breadth = sentiment_breadth([entity, sector, market])
    assert sum(breadth[f"{x}_entity_share"] for x in
               ("positive", "negative", "mixed", "unknown")) == 1


def test_qa_reports_unknown_abstention_duplicates_and_model_disagreement():
    duplicate = observation(cluster="same")
    snapshot = build_psychology_snapshot(NOW, scope="ENTITY", scope_id="RELIANCE",
                                         observations=[duplicate, duplicate.model_copy(
                                             update={"source_id": "rewrite"})])
    metrics = psychology_qa(list(snapshot.observations), [snapshot], model_disagreements=1)
    assert metrics["duplicate_suppression_rate"] == 0.5
    assert metrics["abstention_rate"] == 1
    assert metrics["model_disagreement_rate"] == 0.5


def test_adversarial_and_null_fixtures_do_not_encode_extremes():
    fixtures = psychology_fixture_cases()
    null = null_psychology_fixture()
    assert len(fixtures) == 216 and len(null) == 200
    assert {x["case"] for x in fixtures} >= {"sarcasm", "prompt injection", "LLM disagreement",
                                             "duplicate syndication", "rumour repeated as fact"}
    assert max(sum(x["direction"] == direction for x in null)
               for direction in {x["direction"] for x in null}) == 50


def test_social_sources_are_candidates_only_with_policy_boundaries():
    sources = psychology_source_candidates()
    assert all(not x.activated for x in sources)
    assert {x.source_id for x in sources} == {
        "google-trends-api-alpha", "reddit-data-api", "youtube-data-api"}
    reddit = next(x for x in sources if x.source_id == "reddit-data-api")
    assert "COMMERCIAL_APPROVAL" in reddit.rights_status and "honour deletion" in reddit.privacy_requirements
