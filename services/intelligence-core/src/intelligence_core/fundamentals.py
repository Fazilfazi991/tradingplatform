from __future__ import annotations

from datetime import datetime
from decimal import Decimal, DivisionByZero
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator
from research_core.common import stable_hash

from intelligence_core.models import FrozenModel


class PeriodType(StrEnum):
    QUARTERLY = "QUARTERLY"
    HALF_YEAR = "HALF_YEAR"
    ANNUAL = "ANNUAL"
    TTM = "TTM"
    YTD = "YTD"


class StatementType(StrEnum):
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    NOTES = "NOTES"
    SEGMENT = "SEGMENT"
    GUIDANCE = "GUIDANCE"
    MANAGEMENT_COMMENTARY = "MANAGEMENT_COMMENTARY"
    OTHER = "OTHER"


class FundamentalQualityState(StrEnum):
    STRONG = "STRONG"
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    WEAKENING = "WEAKENING"
    WEAK = "WEAK"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class GuidanceDirection(StrEnum):
    RAISED = "RAISED"
    LOWERED = "LOWERED"
    REITERATED = "REITERATED"
    WITHDRAWN = "WITHDRAWN"
    INITIATED = "INITIATED"
    UNKNOWN = "UNKNOWN"


class SurpriseState(StrEnum):
    STRONG_POSITIVE = "STRONG_POSITIVE"
    POSITIVE = "POSITIVE"
    IN_LINE = "IN_LINE"
    NEGATIVE = "NEGATIVE"
    STRONG_NEGATIVE = "STRONG_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class ValuationState(StrEnum):
    LOW_RELATIVE = "LOW_RELATIVE"
    NORMAL = "NORMAL"
    HIGH_RELATIVE = "HIGH_RELATIVE"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class WarningCode(StrEnum):
    CASH_FLOW_DIVERGENCE = "CASH_FLOW_DIVERGENCE"
    RECEIVABLE_STRESS = "RECEIVABLE_STRESS"
    INVENTORY_BUILD = "INVENTORY_BUILD"
    LEVERAGE_INCREASE = "LEVERAGE_INCREASE"
    INTEREST_COVERAGE_WEAK = "INTEREST_COVERAGE_WEAK"
    MARGIN_COMPRESSION = "MARGIN_COMPRESSION"
    DILUTION = "DILUTION"
    GUIDANCE_CUT = "GUIDANCE_CUT"
    ONE_OFF_PROFIT_DEPENDENCE = "ONE_OFF_PROFIT_DEPENDENCE"
    RESTATEMENT = "RESTATEMENT"
    HIGH_OTHER_INCOME = "HIGH_OTHER_INCOME"
    DATA_INCOMPLETE = "DATA_INCOMPLETE"


class FundamentalObservation(FrozenModel):
    observation_id: UUID = Field(default_factory=uuid4)
    entity_id: str
    metric_id: str
    metric_name: str
    statement_type: StatementType
    period_type: PeriodType
    period_start: datetime
    period_end: datetime
    reporting_currency: str
    unit: str
    original_value: Decimal
    restated_value: Decimal | None = None
    source_id: str
    source_document_id: str
    reported_at: datetime
    source_available_at: datetime
    system_observed_at: datetime
    restatement_available_at: datetime | None = None
    restatement_reason: str | None = None
    available_at: datetime
    accounting_standard: str
    consolidation_scope: str
    quality: str = "PASS"
    provenance: dict[str, Any]
    version: str = "1"
    payload_hash: str = ""

    @model_validator(mode="after")
    def validate_timeline(self) -> FundamentalObservation:
        if self.period_start > self.period_end:
            raise ValueError("period_start must not follow period_end")
        if self.reported_at < self.period_end:
            raise ValueError("reported_at cannot precede period_end")
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("available_at must reflect when this system could know the filing")
        if self.restated_value is not None and self.restatement_available_at is None:
            raise ValueError("restated_value requires restatement_available_at")
        if self.restatement_available_at and self.restatement_available_at < self.available_at:
            raise ValueError("restatement cannot predate the original observation")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(self.model_dump(
                exclude={"payload_hash", "observation_id"}, mode="json"
            )))
        return self

    def value_known_at(self, cutoff: datetime) -> Decimal | None:
        if cutoff < self.available_at:
            return None
        if (self.restated_value is not None and self.restatement_available_at is not None
                and cutoff >= self.restatement_available_at):
            return self.restated_value
        return self.original_value


class GuidanceObservation(FrozenModel):
    entity_id: str
    metric: str
    period: str
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    direction: GuidanceDirection = GuidanceDirection.UNKNOWN
    previous_guidance: str | None = None
    change: str | None = None
    source_id: str
    source_document_id: str
    issued_at: datetime
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    confidence: float = Field(ge=0, le=1)
    derivation_kind: str = "ACCOUNTING_DISCLOSURE"

    @model_validator(mode="after")
    def validate_guidance(self) -> GuidanceObservation:
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("guidance available_at is not causal")
        if (self.lower_bound is not None and self.upper_bound is not None
                and self.lower_bound > self.upper_bound):
            raise ValueError("guidance lower_bound exceeds upper_bound")
        return self


class ConsensusObservation(FrozenModel):
    entity_id: str
    metric_id: str
    period: str
    value: Decimal
    source_id: str
    observed_at: datetime
    available_at: datetime
    number_of_analysts: int | None = Field(default=None, ge=1)
    dispersion: Decimal | None = None


class FundamentalSurprise(FrozenModel):
    metric_id: str
    actual: Decimal | None
    expected: Decimal | None
    absolute_surprise: Decimal | None
    percentage_surprise: Decimal | None
    state: SurpriseState


def calculate_surprise(
    actual: FundamentalObservation,
    expectation: ConsensusObservation | None,
) -> FundamentalSurprise:
    if expectation is None or expectation.available_at >= actual.reported_at:
        return FundamentalSurprise(metric_id=actual.metric_id, actual=actual.original_value,
                                   expected=None, absolute_surprise=None,
                                   percentage_surprise=None, state=SurpriseState.UNKNOWN)
    if expectation.metric_id != actual.metric_id or expectation.period != period_key(actual):
        return FundamentalSurprise(metric_id=actual.metric_id, actual=actual.original_value,
                                   expected=None, absolute_surprise=None,
                                   percentage_surprise=None, state=SurpriseState.UNKNOWN)
    delta = actual.original_value - expectation.value
    pct = safe_ratio(delta, abs(expectation.value))
    state = SurpriseState.IN_LINE
    if pct is not None:
        state = (SurpriseState.STRONG_POSITIVE if pct >= Decimal("0.1") else
                 SurpriseState.POSITIVE if pct > Decimal("0.02") else
                 SurpriseState.STRONG_NEGATIVE if pct <= Decimal("-0.1") else
                 SurpriseState.NEGATIVE if pct < Decimal("-0.02") else SurpriseState.IN_LINE)
    return FundamentalSurprise(metric_id=actual.metric_id, actual=actual.original_value,
                               expected=expectation.value, absolute_surprise=delta,
                               percentage_surprise=pct, state=state)


class PeerGroup(FrozenModel):
    company: str
    peer: str
    relationship: str
    sector: str
    industry: str
    business_similarity: Decimal = Field(ge=0, le=1)
    source_method: str
    valid_from: datetime
    valid_to: datetime | None = None
    version: str = "1"


class CapitalAllocationState(FrozenModel):
    entity_id: str
    as_of: datetime
    capex: Decimal | None = None
    acquisitions: Decimal | None = None
    dividends: Decimal | None = None
    buybacks: Decimal | None = None
    debt_reduction: Decimal | None = None
    fundraising: Decimal | None = None
    equity_dilution: Decimal | None = None
    interpretation: FundamentalQualityState = FundamentalQualityState.UNKNOWN
    evidence_ids: tuple[str, ...] = ()


class ValuationObservation(FrozenModel):
    entity_id: str
    metric: str
    value: Decimal | None
    price_available_at: datetime | None = None
    fundamental_available_at: datetime
    methodology_version: str
    historical_percentile: Decimal | None = Field(default=None, ge=0, le=100)
    sector_percentile: Decimal | None = Field(default=None, ge=0, le=100)
    peer_percentile: Decimal | None = Field(default=None, ge=0, le=100)
    state: ValuationState = ValuationState.UNKNOWN
    provenance: dict[str, Any]

    @model_validator(mode="after")
    def require_price(self) -> ValuationObservation:
        if self.value is not None and self.price_available_at is None:
            raise ValueError("valuation requires a valid point-in-time market price")
        return self


class FundamentalWarning(FrozenModel):
    code: WarningCode
    description: str
    evidence_ids: tuple[str, ...]
    severity: str
    language: str = "potential accounting-quality concern; requires review"


class AxisEvidence(FrozenModel):
    state: FundamentalQualityState = FundamentalQualityState.UNKNOWN
    evidence_ids: tuple[str, ...] = ()
    explanation: tuple[str, ...] = ()


class FundamentalSnapshot(FrozenModel):
    entity_id: str
    cutoff: datetime
    latest_known_financials: tuple[FundamentalObservation, ...]
    prior_comparable_periods: tuple[FundamentalObservation, ...]
    guidance: tuple[GuidanceObservation, ...]
    warnings: tuple[FundamentalWarning, ...]
    valuation: tuple[ValuationObservation, ...]
    source_health: dict[str, str]
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def set_hash(self) -> FundamentalSnapshot:
        all_available = [o.available_at <= self.cutoff for o in (*self.latest_known_financials,
                                                                   *self.prior_comparable_periods)]
        if not all(all_available):
            raise ValueError("snapshot contains future filing leakage")
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class FundamentalEvidence(FrozenModel):
    engine_id: str = "fundamental-evidence-engine"
    engine_version: str = "1"
    entity: str
    as_of: datetime
    horizon: str
    status: str
    growth_state: AxisEvidence
    margin_state: AxisEvidence
    profitability_state: AxisEvidence
    cash_flow_state: AxisEvidence
    balance_sheet_state: AxisEvidence
    working_capital_state: AxisEvidence
    capital_efficiency_state: AxisEvidence
    guidance_state: AxisEvidence
    earnings_quality_state: AxisEvidence
    valuation_state: AxisEvidence
    positive_evidence: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    mixed_evidence: tuple[str, ...]
    warnings: tuple[FundamentalWarning, ...]
    contradictions: tuple[str, ...]
    certainty: float = Field(ge=0, le=1)
    data_quality: str
    directional_evidence_score: Decimal | None = None
    explanation_payload: dict[str, Any]
    provenance: dict[str, Any]


def period_key(item: FundamentalObservation) -> str:
    return f"{item.period_type}:{item.period_end.date().isoformat()}"


def safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    try:
        return numerator / denominator if denominator else None
    except (DivisionByZero, ZeroDivisionError):
        return None


def growth(current: FundamentalObservation, prior: FundamentalObservation) -> Decimal:
    _compatible(current, prior)
    value = safe_ratio(current.original_value - prior.original_value, abs(prior.original_value))
    if value is None:
        raise ValueError("growth is undefined for a zero prior value")
    return value


def margin(profit: Decimal, revenue: Decimal) -> Decimal | None:
    return safe_ratio(profit, revenue)


def return_on_equity(profit: Decimal, opening_equity: Decimal,
                     closing_equity: Decimal) -> Decimal | None:
    return safe_ratio(profit, (opening_equity + closing_equity) / Decimal(2))


def return_on_capital_employed(ebit: Decimal, assets: Decimal,
                               current_liabilities: Decimal) -> Decimal | None:
    return safe_ratio(ebit, assets - current_liabilities)


def free_cash_flow(operating_cash_flow: Decimal, capex: Decimal) -> Decimal:
    return operating_cash_flow - abs(capex)


def working_capital_days(balance: Decimal, flow: Decimal, days: int = 365) -> Decimal | None:
    ratio = safe_ratio(balance, flow)
    return ratio * Decimal(days) if ratio is not None else None


def _compatible(current: FundamentalObservation, prior: FundamentalObservation) -> None:
    fields = ("entity_id", "metric_id", "period_type", "reporting_currency", "unit",
              "consolidation_scope", "accounting_standard")
    mismatches = [name for name in fields if getattr(current, name) != getattr(prior, name)]
    if mismatches:
        raise ValueError(f"incompatible observations: {', '.join(mismatches)}")


def build_fundamental_snapshot(
    entity: str,
    cutoff: datetime,
    observations: list[FundamentalObservation],
    *,
    guidance: list[GuidanceObservation] | None = None,
    valuations: list[ValuationObservation] | None = None,
    source_health: dict[str, str] | None = None,
) -> FundamentalSnapshot:
    known = [o for o in observations if o.entity_id == entity and o.available_at <= cutoff]
    by_metric: dict[tuple[str, PeriodType, str], list[FundamentalObservation]] = {}
    for item in known:
        by_metric.setdefault((item.metric_id, item.period_type, item.consolidation_scope), []).append(item)
    latest, prior = [], []
    for items in by_metric.values():
        ordered = sorted(items, key=lambda x: (x.period_end, x.available_at), reverse=True)
        latest.append(ordered[0])
        prior.extend(ordered[1:2])
    known_guidance = tuple(g for g in (guidance or []) if g.entity_id == entity and g.available_at <= cutoff)
    known_valuations = tuple(v for v in (valuations or []) if v.entity_id == entity
                             and v.fundamental_available_at <= cutoff
                             and (v.price_available_at is None or v.price_available_at <= cutoff))
    warnings = detect_warnings(latest, prior, known_guidance)
    return FundamentalSnapshot(entity_id=entity, cutoff=cutoff,
                               latest_known_financials=tuple(sorted(latest, key=lambda x: x.metric_id)),
                               prior_comparable_periods=tuple(sorted(prior, key=lambda x: x.metric_id)),
                               guidance=known_guidance, warnings=warnings,
                               valuation=known_valuations, source_health=source_health or {})


def detect_warnings(
    latest: list[FundamentalObservation],
    prior: list[FundamentalObservation],
    guidance: tuple[GuidanceObservation, ...] = (),
) -> tuple[FundamentalWarning, ...]:
    current = {x.metric_id: x for x in latest}
    previous = {x.metric_id: x for x in prior}
    result: list[FundamentalWarning] = []
    def add(code: WarningCode, text: str, *items: FundamentalObservation) -> None:
        result.append(FundamentalWarning(code=code, description=text,
                                        evidence_ids=tuple(str(x.observation_id) for x in items),
                                        severity="REVIEW"))
    pat, cfo = current.get("PAT"), current.get("OPERATING_CASH_FLOW")
    if pat and cfo and pat.original_value > 0 and cfo.original_value / pat.original_value < Decimal("0.6"):
        add(WarningCode.CASH_FLOW_DIVERGENCE, "Operating cash flow is materially below reported profit", pat, cfo)
    revenue, receivables = current.get("REVENUE"), current.get("RECEIVABLES")
    old_revenue, old_receivables = previous.get("REVENUE"), previous.get("RECEIVABLES")
    if (revenue and receivables and old_revenue and old_receivables
            and growth(receivables, old_receivables)
            - growth(revenue, old_revenue) > Decimal("0.15")):
        add(WarningCode.RECEIVABLE_STRESS,
            "Receivables growth materially exceeds revenue growth", revenue, receivables)
    debt, old_debt = current.get("DEBT"), previous.get("DEBT")
    if debt and old_debt and growth(debt, old_debt) > Decimal("0.2"):
        add(WarningCode.LEVERAGE_INCREASE, "Debt increased materially", debt, old_debt)
    for item in latest:
        if item.restated_value is not None:
            add(WarningCode.RESTATEMENT, "A later restatement exists; review reason and timing", item)
    if any(g.direction == GuidanceDirection.LOWERED for g in guidance):
        result.append(FundamentalWarning(code=WarningCode.GUIDANCE_CUT,
                                         description="Management lowered disclosed guidance",
                                         evidence_ids=tuple(g.source_document_id for g in guidance
                                                            if g.direction == GuidanceDirection.LOWERED),
                                         severity="REVIEW"))
    if not latest:
        result.append(FundamentalWarning(code=WarningCode.DATA_INCOMPLETE,
                                         description="No point-in-time financial observations available",
                                         evidence_ids=(), severity="DATA"))
    return tuple(result)


class FundamentalEvidenceEngine:
    def evaluate(self, snapshot: FundamentalSnapshot, *, horizon: str) -> FundamentalEvidence:
        unknown = AxisEvidence()
        warning_codes = {warning.code for warning in snapshot.warnings}
        cash = AxisEvidence(state=FundamentalQualityState.WEAKENING,
                            evidence_ids=tuple(e for w in snapshot.warnings
                                               if w.code == WarningCode.CASH_FLOW_DIVERGENCE
                                               for e in w.evidence_ids),
                            explanation=("Cash generation diverges from profit",)) \
            if WarningCode.CASH_FLOW_DIVERGENCE in warning_codes else unknown
        balance = AxisEvidence(state=FundamentalQualityState.WEAKENING,
                               explanation=("Leverage increased",)) \
            if WarningCode.LEVERAGE_INCREASE in warning_codes else unknown
        guidance = AxisEvidence(state=FundamentalQualityState.WEAKENING,
                                explanation=("Management guidance was lowered",)) \
            if WarningCode.GUIDANCE_CUT in warning_codes else unknown
        quality = AxisEvidence(state=FundamentalQualityState.WEAKENING,
                               explanation=("Accounting-quality warning requires review",)) \
            if warning_codes - {WarningCode.DATA_INCOMPLETE} else unknown
        coverage = len(snapshot.latest_known_financials)
        return FundamentalEvidence(
            entity=snapshot.entity_id, as_of=snapshot.cutoff, horizon=horizon,
            status="INTERNAL_FUNDAMENTAL_EVIDENCE_NOT_PREDICTION",
            growth_state=unknown, margin_state=unknown, profitability_state=unknown,
            cash_flow_state=cash, balance_sheet_state=balance, working_capital_state=unknown,
            capital_efficiency_state=unknown, guidance_state=guidance,
            earnings_quality_state=quality, valuation_state=unknown,
            positive_evidence=(), negative_evidence=tuple(w.description for w in snapshot.warnings),
            mixed_evidence=(), warnings=snapshot.warnings, contradictions=(),
            certainty=min(1.0, coverage / 12),
            data_quality="FIXTURE_PASS" if coverage else "INSUFFICIENT_DATA",
            directional_evidence_score=None,
            explanation_payload={"label": "INTERNAL INTELLIGENCE — NOT PREDICTION",
                                 "not": ["stock return probability", "expected return", "buy/sell"]},
            provenance={"snapshot_hash": snapshot.snapshot_hash, "mode": "ENGINEERING_FIXTURE"},
        )


def fundamental_qa_metrics(observations: list[FundamentalObservation], *,
                           expected_metrics: int, now: datetime) -> dict[str, float | int]:
    sources: dict[tuple[str, str, str], set[str]] = {}
    for item in observations:
        sources.setdefault((item.entity_id, item.metric_id, period_key(item)), set()).add(item.source_id)
    return {
        "coverage": min(1.0, len({o.metric_id for o in observations}) / expected_metrics)
        if expected_metrics else 1.0,
        "missing_periods": max(0, expected_metrics - len({o.metric_id for o in observations})),
        "restatement_rate": sum(o.restated_value is not None for o in observations) / len(observations)
        if observations else 0,
        "source_conflicts": sum(len(value) > 1 for value in sources.values()),
        "stale_observations": sum((now - o.available_at).days > 550 for o in observations),
    }
