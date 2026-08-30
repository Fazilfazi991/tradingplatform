from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from intelligence_core.macro import (
    SECTOR_EXPOSURES,
    CrossMarketState,
    MacroCategory,
    MacroEvidenceEngine,
    MacroExpectation,
    MacroObservation,
    MacroRegime,
    MarketState,
    MonetaryPolicyState,
    RiskState,
    TrendState,
    build_macro_snapshot,
    classify_rbi_event,
    classify_risk_state,
    default_unknown_state,
    macro_contradictions,
    macro_qa_metrics,
    normalize_unit,
)
from intelligence_core.macro_fixtures import macro_fixture_observations
from intelligence_core.macro_sources import macro_source_candidates

RELEASE = datetime(2026, 1, 31, 10, tzinfo=UTC)
OBSERVED = RELEASE + timedelta(minutes=20)


def observation(**updates):
    values = {
        "indicator_id": "GDP-IN-Q1",
        "indicator_name": "India GDP",
        "category": MacroCategory.GDP,
        "country": "IN",
        "region": "INDIA",
        "source_id": "MOSPI_FIXTURE",
        "period": "2026-Q1",
        "frequency": "QUARTERLY",
        "unit": "PERCENT",
        "original_value": Decimal("6.1"),
        "release_time": RELEASE,
        "source_available_at": RELEASE,
        "system_observed_at": OBSERVED,
        "available_at": OBSERVED,
        "provenance": {"mode": "FIXTURE"},
    }
    values.update(updates)
    return MacroObservation(**values)


def states(at=OBSERVED):
    policy, cross, regime = default_unknown_state(at)
    return policy, cross, regime


def test_original_value_survives_revision_and_timeline_reconstruction():
    item = observation(
        revised_value=Decimal("5.8"),
        revision_available_at=OBSERVED + timedelta(days=30),
    )
    assert item.original_value == Decimal("6.1")
    assert item.value_known_at(RELEASE + timedelta(minutes=10)) is None
    assert item.value_known_at(OBSERVED) == Decimal("6.1")
    assert item.value_known_at(OBSERVED + timedelta(days=31)) == Decimal("5.8")


def test_consensus_must_predate_release_and_surprise_uses_original():
    expected = MacroExpectation(
        value=Decimal("6.0"),
        source_id="CONSENSUS_FIXTURE",
        available_at=RELEASE - timedelta(hours=1),
    )
    assert observation(expectation=expected).surprise() == "POSITIVE_SURPRISE"
    with pytest.raises(ValueError, match="before release"):
        observation(expectation=expected.model_copy(update={"available_at": RELEASE}))
    assert observation().surprise() == "UNKNOWN"


def test_causal_times_and_revision_validation():
    with pytest.raises(ValueError, match="system could know"):
        observation(available_at=RELEASE)
    with pytest.raises(ValueError, match="revision_available_at"):
        observation(revised_value=Decimal("5.8"))


def test_unit_normalization_rejects_ambiguity():
    assert normalize_unit(Decimal(25), "bps") == (Decimal(25), "BASIS_POINTS")
    assert normalize_unit(Decimal("6.1"), "%") == (Decimal("6.1"), "PERCENT")
    with pytest.raises(ValueError, match="ambiguous"):
        normalize_unit(Decimal(1), "points maybe")


def test_risk_state_and_cross_market_disagreement():
    def market(name, risk):
        return MarketState(
            name=name,
            category=MacroCategory.GLOBAL_EQUITY,
            latest_completed_session=RELEASE,
            risk_state=risk,
            source_id="FIXTURE",
            source_available_at=RELEASE,
            system_observed_at=OBSERVED,
            quality="PASS",
        )

    assert classify_risk_state([])[0] == RiskState.UNKNOWN
    assert classify_risk_state([market("US", RiskState.RISK_ON)])[0] == RiskState.RISK_ON
    state, explanation = classify_risk_state(
        [market("US", RiskState.RISK_ON), market("ASIA", RiskState.RISK_OFF)]
    )
    assert state == RiskState.MIXED and "disagree" in explanation[0]


def test_multi_axis_regime_preserves_contradictions():
    regime = MacroRegime(
        growth="ACCELERATING",
        inflation="FALLING",
        policy="FX_STRESS",
        liquidity="TIGHTENING",
        global_risk=RiskState.RISK_ON,
        commodity_pressure="HIGH",
    )
    assert len(macro_contradictions(regime)) == 3


def test_snapshot_cutoff_hash_and_macro_evidence_are_not_predictions():
    policy, cross, _regime = states()
    regime = MacroRegime(growth="ACCELERATING", liquidity="TIGHTENING")
    late = observation(
        indicator_id="LATE",
        source_available_at=OBSERVED + timedelta(hours=1),
        system_observed_at=OBSERVED + timedelta(hours=2),
        available_at=OBSERVED + timedelta(hours=2),
    )
    snapshot = build_macro_snapshot(
        OBSERVED,
        [observation(), late],
        policy_state=policy,
        cross_market=cross,
        regime=regime,
        source_health={"rbi": "HEALTHY"},
    )
    assert len(snapshot.observations) == 1 and snapshot.snapshot_hash
    result = MacroEvidenceEngine().evaluate(snapshot, horizon="1D")
    assert result.directional_evidence_score is None
    assert "stock return probability" in result.explanation_payload["not"]


def test_policy_liquidity_fx_rates_commodity_and_global_contracts():
    policy = MonetaryPolicyState(
        policy_rate_direction=TrendState.RISING,
        stance="TIGHT",
        liquidity_bias="TIGHTENING",
        inflation_bias="ELEVATED",
        growth_bias="NEUTRAL",
        financial_conditions="TIGHTENING",
        certainty=0.8,
        source_quality="OFFICIAL",
        as_of=OBSERVED,
    )
    cross = CrossMarketState(
        as_of=OBSERVED,
        india_market_context="UNKNOWN",
        global_equity_state="RISK_OFF",
        rates_state="RISING",
        fx_state="INR_WEAKENING",
        commodity_state="CRUDE_PRESSURE_HIGH",
        volatility_state="EXPANDING",
        risk_state=RiskState.RISK_OFF,
        contradictions=(),
        data_quality="FIXTURE_PASS",
        source_health={"fixture": "HEALTHY"},
        provenance={"mode": "FIXTURE"},
    )
    assert policy.stance == "TIGHT" and cross.risk_state == RiskState.RISK_OFF
    assert {item.sector for item in SECTOR_EXPOSURES} >= {
        "BANKS",
        "IT",
        "PHARMA",
        "AUTO",
        "FMCG",
        "METALS",
        "ENERGY",
        "REAL_ESTATE",
        "INFRASTRUCTURE",
        "AIRLINES",
        "PAINTS",
        "LOGISTICS",
    }


def test_rbi_event_classification_is_deterministic_and_can_abstain():
    assert classify_rbi_event("Variable Rate Reverse Repo under LAF") == "LIQUIDITY_OPERATION"
    assert classify_rbi_event("Directions under Section 35 A") == "BANKING_REGULATION"
    assert classify_rbi_event("Unrelated administrative notice") == "OTHER"


def test_fixture_has_150_controlled_and_adversarial_cases():
    fixtures = macro_fixture_observations()
    assert len(fixtures) == 150
    cases = {item["case"] for item in fixtures}
    assert {
        "rate hike",
        "rate cut",
        "future consensus leakage",
        "unit mismatch",
        "conflicting sources",
    } <= cases


def test_macro_qa_metrics_report_coverage_staleness_and_revisions():
    item = observation()
    metrics = macro_qa_metrics([item], expected_indicators=2, now=OBSERVED)
    assert metrics["macro_coverage"] == 0.5
    assert metrics["revision_correctness"] == 1
    assert metrics["stale_indicator_rate"] == 0


def test_macro_source_candidates_are_provider_agnostic_and_not_activated():
    candidates = macro_source_candidates()
    assert {candidate.source_id for candidate in candidates} >= {
        "rbi-dbie",
        "mospi-releases",
        "fred-alfred",
        "us-bls-api",
        "us-bea-api",
    }
    assert all(not candidate.activated for candidate in candidates)
    assert any(candidate.revision_capable for candidate in candidates)
