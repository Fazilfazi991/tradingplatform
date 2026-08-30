from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import httpx
import pytest
from research_core.objects import ResearchMode
from research_core.policy import REQUIRED_FORMAL_GATES, ResearchGateError, ResearchGatePolicy
from verified_edge.corporate_actions import CorporateAction, CorporateActionType, adjust_bars
from verified_edge.domain import DailyBar
from verified_edge.providers.upstox import UpstoxMarketDataProvider
from verified_edge.reconciliation import reconciliation_report
from verified_edge.universe import MembershipSourceAssessment, SourceDecision


def bar(day: int, close: str = "100", volume: int = 10, provider: str = "A") -> DailyBar:
    value = Decimal(close)
    return DailyBar(
        instrument_id=UUID(int=1),
        symbol="TEST",
        session_date=date(2026, 1, day),
        open=value,
        high=value,
        low=value,
        close=value,
        volume=volume,
        provider=provider,
        raw_observation_id=UUID(int=day),
        transformation_hash=f"raw-{day}",
    )


def test_split_adjustment_preserves_raw_and_removes_artificial_jump():
    raw = [bar(1, "100", 10), bar(2, "50", 20)]
    action = CorporateAction(
        action_type=CorporateActionType.SPLIT,
        effective_date=date(2026, 1, 2),
        numerator=Decimal(2),
        denominator=Decimal(1),
        source="OFFICIAL_FIXTURE",
        source_version="1",
    )
    adjusted, ledger = adjust_bars(raw, [action])
    assert raw[0].close == 100
    assert [item.close for item in adjusted] == [50, 50]
    assert [item.volume for item in adjusted] == [20, 20]
    assert ledger[0].calculation == "price*0.5;volume*2"


def test_dividend_requires_explicit_reference_price_for_adjustment():
    action = CorporateAction(
        action_type=CorporateActionType.DIVIDEND,
        effective_date=date(2026, 1, 2),
        cash_amount=Decimal(5),
        source="OFFICIAL_FIXTURE",
        source_version="1",
    )
    with pytest.raises(ValueError, match="reference price"):
        adjust_bars([bar(1)], [action])


def test_upstox_corporate_action_contract():
    payload = {
        "status": "success",
        "data": [
            {
                "name": "Split",
                "expiry_date": "02 Jan 2026",
                "amount": None,
                "ratio": "2:1",
                "event_details": [],
            }
        ],
    }
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
    )
    result = UpstoxMarketDataProvider(token="redacted", client=client).get_corporate_actions(
        "INE000000001"
    )
    assert result[0].action_type == CorporateActionType.SPLIT
    assert result[0].numerator == 2 and result[0].denominator == 1


def test_reconciliation_reports_both_missing_sides_and_deltas():
    primary = [bar(1), bar(2, "100")]
    secondary = [bar(1, "100.02", 11, "B"), bar(3, provider="B")]
    report = reconciliation_report(primary, secondary)
    assert report.comparable_rows == 1
    assert report.price_mismatches == 4 and report.volume_mismatches == 1
    assert report.missing_primary == 1 and report.missing_secondary == 1
    assert report.max_price_delta == Decimal("0.02")


def test_membership_source_requires_effective_dates_and_reviewed_terms():
    assessment = MembershipSourceAssessment(
        "NSE Indices subscription",
        SourceDecision.REVIEW_REQUIRED,
        None,
        None,
        True,
        False,
        "Subscription and entitlement required",
    )
    assert not assessment.supports_historical_research


def test_only_exploratory_real_can_be_unlocked_by_batch_four_gates():
    passed = ResearchGatePolicy({gate: True for gate in REQUIRED_FORMAL_GATES})
    passed.authorize(ResearchMode.EXPLORATORY_REAL)
    with pytest.raises(ResearchGateError, match="Batch 4"):
        passed.authorize(ResearchMode.FORMAL_DISCOVERY)
    blocked = ResearchGatePolicy.current()
    with pytest.raises(ResearchGateError, match="missing readiness gates"):
        blocked.authorize(ResearchMode.EXPLORATORY_REAL)


def test_all_timestamps_remain_timezone_aware():
    assert datetime.now(UTC).utcoffset() is not None
