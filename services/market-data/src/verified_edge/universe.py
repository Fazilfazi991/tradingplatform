from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import median

from verified_edge.domain import DailyBar, Instrument, UniverseDefinition

NIFTY200_V1 = UniverseDefinition(
    membership_source="WRITTEN/LICENCED POINT-IN-TIME SOURCE REQUIRED",
    effective_from=date(2026, 8, 30),
    point_in_time_complete=False,
)


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reasons: tuple[str, ...]


def evaluate_eligibility(
    instrument: Instrument,
    history: list[DailyBar],
    unresolved_critical_incident: bool,
    definition: UniverseDefinition = NIFTY200_V1,
) -> EligibilityResult:
    reasons = []
    if instrument.exchange != "NSE" or instrument.instrument_type != "EQUITY":
        reasons.append("NOT_NSE_EQUITY")
    if instrument.listing_status != "ACTIVE":
        reasons.append("NOT_ACTIVE")
    if len(history) < definition.min_prior_sessions:
        reasons.append("INSUFFICIENT_HISTORY")
    if history:
        latest = max(history, key=lambda bar: bar.session_date)
        if latest.close < definition.min_close_inr:
            reasons.append("PRICE_BELOW_FLOOR")
        recent = sorted(history, key=lambda bar: bar.session_date)[-20:]
        traded_values = [bar.close * Decimal(bar.volume) for bar in recent]
        if (
            len(traded_values) < 20
            or median(traded_values) < definition.min_median_traded_value_inr
        ):
            reasons.append("LIQUIDITY_BELOW_FLOOR")
    if unresolved_critical_incident:
        reasons.append("UNRESOLVED_CRITICAL_DATA_INCIDENT")
    return EligibilityResult(not reasons, tuple(reasons))
