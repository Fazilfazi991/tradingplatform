from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from intelligence_core.positioning import (
    BasisState,
    DealObservation,
    DeliveryObservation,
    ExpiryType,
    FlowDerivativesEvidenceEngine,
    FlowObservation,
    FlowType,
    FuturesObservation,
    OptionObservation,
    OptionType,
    ParticipantType,
    RolloverState,
    basis_state,
    build_derivatives_snapshot,
    build_flow_snapshot,
    build_option_chain,
    normalize_flows,
    option_concentration,
    option_skew,
    pcr,
    positioning_qa,
    price_oi_quadrant,
)
from intelligence_core.positioning_fixtures import (
    null_positioning_fixture,
    positioning_fixture_cases,
)
from intelligence_core.positioning_sources import positioning_source_candidates
from intelligence_core.specialist_engines import specialist_engine_registry

NOW = datetime(2026, 8, 30, 12, tzinfo=UTC)
EXPIRY = datetime(2026, 9, 24, 15, 30, tzinfo=UTC)


def flow(net="20", available=NOW, **updates):
    values = {"scope": "MARKET", "market_id": "INDIA", "flow_type": FlowType.CASH_MARKET,
              "participant_type": ParticipantType.FII, "buy_value": Decimal(60),
              "sell_value": Decimal(40), "net_value": Decimal(net), "gross_value": Decimal(100),
              "currency": "INR_CRORE", "period_start": NOW - timedelta(hours=6),
              "period_end": NOW, "source_id": "FIXTURE", "source_available_at": available,
              "system_observed_at": available, "available_at": available,
              "provenance": {"mode": "ENGINEERING_FIXTURE"}}
    values.update(updates)
    return FlowObservation(**values)


def future(close="101", spot="100", available=NOW, **updates):
    values = {"instrument_id": "NIFTY-FUT", "underlying": "NIFTY", "contract_id": "NIFTY-SEP",
              "expiry": EXPIRY, "timestamp": NOW, "open": Decimal(100), "high": Decimal(102),
              "low": Decimal(99), "close": Decimal(close), "volume": Decimal(1000),
              "open_interest": Decimal(5000), "change_in_open_interest": Decimal(100),
              "underlying_price": Decimal(spot), "basis": Decimal(close) - Decimal(spot),
              "days_to_expiry": 25, "source_id": "FIXTURE", "source_available_at": available,
              "system_observed_at": available, "available_at": available, "provenance": {}}
    values.update(updates)
    return FuturesObservation(**values)


def option(kind="CALL", strike="100", iv="20", contract=None, available=NOW, **updates):
    option_type = OptionType(kind)
    values = {"underlying": "NIFTY", "contract_id": contract or f"{kind}-{strike}",
              "expiry": EXPIRY, "expiry_type": ExpiryType.MONTHLY, "strike": Decimal(strike),
              "option_type": option_type, "timestamp": NOW, "bid": Decimal(5), "ask": Decimal(6),
              "last_price": Decimal("5.5"), "volume": Decimal(100),
              "open_interest": Decimal(200 if option_type == OptionType.PUT else 100),
              "change_in_open_interest": Decimal(20 if option_type == OptionType.PUT else 10),
              "implied_volatility": Decimal(iv), "underlying_price": Decimal(100),
              "moneyness": Decimal(strike) - Decimal(100), "days_to_expiry": 25,
              "source_id": "FIXTURE", "source_available_at": available,
              "system_observed_at": available, "available_at": available, "provenance": {}}
    values.update(updates)
    return OptionObservation(**values)


def chain(options=None):
    items = options or [option("CALL", "95"), option("PUT", "95", "25"),
                        option("CALL", "100"), option("PUT", "100", "25"),
                        option("CALL", "105"), option("PUT", "105", "25")]
    return build_option_chain("NIFTY", EXPIRY, NOW, items, spot=Decimal(100), source_id="FIXTURE")


def test_flow_is_causal_and_values_reconcile():
    assert flow().payload_hash
    with pytest.raises(ValueError, match="publication"):
        flow(available=NOW, source_available_at=NOW, system_observed_at=NOW + timedelta(minutes=1))
    with pytest.raises(ValueError, match="net_value"):
        flow(net="21")


def test_late_eod_flow_cannot_enter_intraday_snapshot():
    late = flow(available=NOW + timedelta(hours=6))
    snapshot = build_flow_snapshot("MARKET", "INDIA", NOW, [flow(), late])
    assert len(snapshot.institutional_flows) == 1 and snapshot.snapshot_hash


def test_flow_normalization_requires_history_and_is_not_return_optimized():
    history = [flow(net=str(x), buy_value=Decimal(50 + x / 2), sell_value=Decimal(50 - x / 2),
                    period_start=NOW - timedelta(days=i + 1), period_end=NOW - timedelta(days=i + 1))
               for i, x in enumerate((10, 20, -10, 5, -5))]
    result = normalize_flows(flow(), history)
    assert result["normalized"] == Decimal("0.2")
    assert result["percentile"] == Decimal(1)
    assert normalize_flows(flow(), history[:2])["zscore"] is None


def test_delivery_and_deal_contracts_do_not_infer_intent():
    delivery = DeliveryObservation(entity_id="RELIANCE", trading_date=NOW,
        delivery_quantity=Decimal(60), delivery_percentage=Decimal(60),
        traded_quantity=Decimal(100), traded_value=Decimal(1000), turnover=Decimal(1000),
        source_id="FIXTURE", source_available_at=NOW, system_observed_at=NOW, available_at=NOW)
    deal = DealObservation(entity_id="RELIANCE", buyer="A", seller="B", quantity=Decimal(10),
        deal_type=FlowType.BLOCK_DEAL, traded_at=NOW, source_id="FIXTURE", available_at=NOW)
    snapshot = build_flow_snapshot("ENTITY", "RELIANCE", NOW, [], deliveries=[delivery], deals=[deal])
    assert snapshot.deliveries[0].delivery_percentage == 60
    assert snapshot.deals[0].interpretation == "UNKNOWN_INTENT"
    with pytest.raises(ValueError, match="block or bulk"):
        deal.model_copy(update={"deal_type": FlowType.CASH_MARKET}).model_validate(
            {**deal.model_dump(), "deal_type": FlowType.CASH_MARKET})


def test_futures_basis_expiry_and_price_oi_are_descriptive_only():
    item = future()
    assert basis_state(item) == BasisState.PREMIUM
    assert basis_state(future(close="99")) == BasisState.DISCOUNT
    assert basis_state(future(close="100")) == BasisState.NEAR_FAIR
    assert price_oi_quadrant(Decimal(101), Decimal(100), Decimal(20)) == "PRICE_UP_OI_UP"
    assert price_oi_quadrant(None, Decimal(100), Decimal(20)) == "UNKNOWN"
    with pytest.raises(ValueError, match="days_to_expiry"):
        future(days_to_expiry=24)


def test_rollover_contract_is_activity_not_sentiment():
    state = RolloverState(underlying="NIFTY", near_expiry=EXPIRY,
        next_expiry=EXPIRY + timedelta(days=28), near_month_oi=Decimal(100),
        next_month_oi=Decimal(80), roll_activity=Decimal(30),
        roll_percentage=Decimal("0.444"), roll_concentration=Decimal("0.4"), as_of=NOW)
    assert "NOT_SENTIMENT" in state.interpretation


def test_option_contract_enforces_expiry_spread_and_corporate_action_reference():
    assert option().days_to_expiry == 25
    with pytest.raises(ValueError, match="bid exceeds"):
        option(bid=Decimal(7), ask=Decimal(6))
    with pytest.raises(ValueError, match="corporate-action"):
        option(adjusted_contract=True)
    assert option(adjusted_contract=True, adjustment_reference="SPLIT-2026").adjusted_contract


def test_chain_is_causal_expiry_specific_deduplicated_and_methodology_defined():
    duplicate = option(contract="CALL-100", open_interest=Decimal(999))
    built = chain([option("CALL", "95"), option("PUT", "95"), option("CALL", "100"),
                   duplicate, option("PUT", "100"), option("CALL", "105"), option("PUT", "105")])
    assert len(built.calls) == 3
    assert built.aggregate_metrics["pcr_interpretation"] == "STRUCTURE_ONLY"
    assert built.quality == "PASS" and built.snapshot_hash


def test_pcr_handles_zero_denominator_and_skew_is_not_prediction():
    puts = [option("PUT", "100", "30")]
    assert pcr(puts, "open_interest") is None
    options = [option("CALL", "100", "20"), option("PUT", "100", "25")]
    difference, state = option_skew(options)
    assert difference == 5 and state == "DOWNSIDE_RICH"
    with pytest.raises(ValueError, match="methodology"):
        pcr(options, "price")


def test_option_concentration_is_positioning_reference_not_barrier():
    result = option_concentration([option("CALL", "100"), option("PUT", "100")])
    assert result["concentration"] == 1
    assert result["label"] == "POSITIONING_REFERENCE_NOT_PRICE_BARRIER"


def test_derivatives_snapshot_and_engine_preserve_ambiguity_and_abstention():
    derivatives = build_derivatives_snapshot("NIFTY", NOW, "NEAREST_MONTHLY", [future()], [chain()])
    flows = build_flow_snapshot("MARKET", "INDIA", NOW, [flow()])
    result = FlowDerivativesEvidenceEngine().evaluate(flows, derivatives, horizon="1D")
    assert result.status == "INTERNAL_POSITIONING_EVIDENCE_NOT_PREDICTION"
    assert result.directional_evidence_score is None
    assert {"hedging", "market making"} <= set(result.explanation_payload["ambiguity"])
    empty = build_flow_snapshot("MARKET", "INDIA", NOW, [])
    assert FlowDerivativesEvidenceEngine().evaluate(empty, None, horizon="1D").status == \
        "INSUFFICIENT_POSITIONING_EVIDENCE"


def test_qa_reports_chain_expiry_iv_participant_and_abstention():
    derivatives = build_derivatives_snapshot("NIFTY", NOW, "NEAREST_MONTHLY", [future()], [chain()])
    flows = build_flow_snapshot("MARKET", "INDIA", NOW, [flow()])
    metrics = positioning_qa(flows, derivatives)
    assert metrics["chain_completeness"] == 1
    assert metrics["strike_coverage"] == 3 and metrics["expiry_coverage"] == 1
    assert metrics["iv_availability"] == 1 and not metrics["abstention"]


def test_fixtures_null_sources_and_seven_engine_registry():
    fixtures, null = positioning_fixture_cases(), null_positioning_fixture()
    assert len(fixtures) == 259 and len(null) == 250
    assert {x["case"] for x in fixtures} >= {"after-close FII data used intraday",
        "zero denominator PCR", "corporate-action strike adjustment", "wrong expiry"}
    assert sum(int(x["net_contracts"]) for x in null) == 0
    sources = positioning_source_candidates()
    assert all(not x.activated and x.review_state == "CANDIDATE" for x in sources)
    registry = specialist_engine_registry()
    assert len(registry) == 7
    assert {x.engine_id for x in registry} == {"TECHNICAL", "HISTORICAL", "NEWS_EVENT",
        "MACRO_GLOBAL", "FUNDAMENTAL", "PSYCHOLOGY", "FLOW_DERIVATIVES"}
    assert all(x.predictive_validation_status == "NOT_STARTED" for x in registry)
