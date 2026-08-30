from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from intelligence_core.fundamental_fixtures import fundamental_fixture_cases
from intelligence_core.fundamental_sources import fundamental_source_candidates
from intelligence_core.fundamentals import (
    ConsensusObservation,
    FundamentalEvidenceEngine,
    FundamentalObservation,
    GuidanceDirection,
    GuidanceObservation,
    PeriodType,
    StatementType,
    ValuationObservation,
    build_fundamental_snapshot,
    calculate_surprise,
    free_cash_flow,
    growth,
    margin,
    return_on_capital_employed,
    return_on_equity,
    working_capital_days,
)
from intelligence_core.llm_analyzer import validate_financial_numbers

END = datetime(2025, 12, 31, tzinfo=UTC)
REPORTED = datetime(2026, 1, 20, 10, tzinfo=UTC)
OBSERVED = REPORTED + timedelta(minutes=5)


def observation(metric="REVENUE", value="100", end=END, **updates):
    values = {
        "entity_id": "RELIANCE", "metric_id": metric, "metric_name": metric.title(),
        "statement_type": StatementType.INCOME_STATEMENT,
        "period_type": PeriodType.QUARTERLY,
        "period_start": end - timedelta(days=90), "period_end": end,
        "reporting_currency": "INR", "unit": "CRORE", "original_value": Decimal(value),
        "source_id": "FIXTURE", "source_document_id": f"doc-{end.date()}-{metric}",
        "reported_at": REPORTED, "source_available_at": REPORTED,
        "system_observed_at": OBSERVED, "available_at": OBSERVED,
        "accounting_standard": "IND_AS", "consolidation_scope": "CONSOLIDATED",
        "provenance": {"mode": "ENGINEERING_FIXTURE"},
    }
    values.update(updates)
    return FundamentalObservation(**values)


def test_observation_timeline_and_immutable_restatement():
    item = observation(restated_value=Decimal(98),
                       restatement_available_at=OBSERVED + timedelta(days=30),
                       restatement_reason="classification correction")
    assert item.value_known_at(REPORTED) is None
    assert item.value_known_at(OBSERVED) == 100
    assert item.value_known_at(OBSERVED + timedelta(days=31)) == 98
    assert item.original_value == 100 and item.payload_hash
    with pytest.raises(ValueError, match="restated_value"):
        observation(restated_value=Decimal(98))


def test_period_unit_currency_scope_and_standard_must_match_for_growth():
    prior = observation(value="80", end=END - timedelta(days=365),
                        reported_at=REPORTED - timedelta(days=365),
                        source_available_at=REPORTED - timedelta(days=365),
                        system_observed_at=OBSERVED - timedelta(days=365),
                        available_at=OBSERVED - timedelta(days=365))
    assert growth(observation(), prior) == Decimal("0.25")
    for change in ({"period_type": PeriodType.ANNUAL}, {"unit": "MILLION"},
                   {"reporting_currency": "USD"}, {"consolidation_scope": "STANDALONE"}):
        with pytest.raises(ValueError, match="incompatible"):
            growth(observation(**change), prior)


def test_calculation_catalog_formulas():
    assert margin(Decimal(20), Decimal(100)) == Decimal("0.2")
    assert return_on_equity(Decimal(20), Decimal(80), Decimal(120)) == Decimal("0.2")
    assert return_on_capital_employed(Decimal(15), Decimal(150), Decimal(50)) == Decimal("0.15")
    assert free_cash_flow(Decimal(30), Decimal(-12)) == Decimal(18)
    assert working_capital_days(Decimal(25), Decimal(100)) == Decimal("91.25")


def test_surprise_requires_valid_pre_release_same_metric_and_period_expectation():
    actual = observation()
    expected = ConsensusObservation(entity_id="RELIANCE", metric_id="REVENUE",
        period="QUARTERLY:2025-12-31", value=Decimal(90), source_id="LICENSED_FIXTURE",
        observed_at=REPORTED - timedelta(days=1), available_at=REPORTED - timedelta(days=1),
        number_of_analysts=8, dispersion=Decimal(2))
    assert calculate_surprise(actual, expected).state == "STRONG_POSITIVE"
    assert calculate_surprise(actual, expected.model_copy(
        update={"available_at": REPORTED})).state == "UNKNOWN"
    assert calculate_surprise(actual, None).expected is None


def test_snapshot_excludes_future_reports_and_uses_comparable_prior():
    prior = observation(value="80", end=END - timedelta(days=365),
                        reported_at=REPORTED - timedelta(days=365),
                        source_available_at=REPORTED - timedelta(days=365),
                        system_observed_at=OBSERVED - timedelta(days=365),
                        available_at=OBSERVED - timedelta(days=365))
    future = observation(metric="PAT", value="12", reported_at=REPORTED + timedelta(days=2),
                         source_available_at=REPORTED + timedelta(days=2),
                         system_observed_at=OBSERVED + timedelta(days=2),
                         available_at=OBSERVED + timedelta(days=2))
    snapshot = build_fundamental_snapshot("RELIANCE", OBSERVED, [prior, observation(), future])
    assert [x.metric_id for x in snapshot.latest_known_financials] == ["REVENUE"]
    assert len(snapshot.prior_comparable_periods) == 1 and snapshot.snapshot_hash


def test_explainable_cash_flow_leverage_and_guidance_warnings_not_prediction():
    prior_end = END - timedelta(days=365)
    prior_times = {"reported_at": REPORTED - timedelta(days=365),
                   "source_available_at": REPORTED - timedelta(days=365),
                   "system_observed_at": OBSERVED - timedelta(days=365),
                   "available_at": OBSERVED - timedelta(days=365)}
    observations = [observation("PAT", "100"), observation("OPERATING_CASH_FLOW", "30",
                    statement_type=StatementType.CASH_FLOW), observation("DEBT", "150",
                    statement_type=StatementType.BALANCE_SHEET),
                    observation("DEBT", "100", end=prior_end, **prior_times)]
    guidance = GuidanceObservation(entity_id="RELIANCE", metric="REVENUE", period="FY2026",
        direction=GuidanceDirection.LOWERED, source_id="FIXTURE", source_document_id="guidance-1",
        issued_at=REPORTED, source_available_at=REPORTED, system_observed_at=OBSERVED,
        available_at=OBSERVED, confidence=1)
    snapshot = build_fundamental_snapshot("RELIANCE", OBSERVED, observations,
                                          guidance=[guidance])
    assert {w.code for w in snapshot.warnings} >= {
        "CASH_FLOW_DIVERGENCE", "LEVERAGE_INCREASE", "GUIDANCE_CUT"}
    evidence = FundamentalEvidenceEngine().evaluate(snapshot, horizon="QUARTERLY")
    assert evidence.directional_evidence_score is None
    assert evidence.status == "INTERNAL_FUNDAMENTAL_EVIDENCE_NOT_PREDICTION"


def test_valuation_refuses_value_without_point_in_time_price():
    with pytest.raises(ValueError, match="market price"):
        ValuationObservation(entity_id="RELIANCE", metric="PE", value=Decimal(20),
            fundamental_available_at=OBSERVED, methodology_version="1", provenance={})


def test_llm_numbers_require_exact_source_span_unit_period_currency():
    spans = ({"source_span_id": "s1", "value": "100", "unit": "CRORE",
              "period": "2025-Q4", "currency": "INR"},)
    validate_financial_numbers({"numeric_facts": [{**spans[0]}]}, spans)
    with pytest.raises(ValueError, match="not grounded"):
        validate_financial_numbers({"numeric_facts": [{**spans[0], "value": "101"}]}, spans)


def test_fixtures_and_sources_are_safely_scoped():
    fixtures = fundamental_fixture_cases()
    assert len(fixtures) == 160
    assert {x["case"] for x in fixtures} >= {"future filing leakage", "LLM invented number",
                                             "bank results", "restatement"}
    sources = fundamental_source_candidates()
    assert all(not source.activated for source in sources)
    assert all("REVIEW" in source.rights_status for source in sources)
