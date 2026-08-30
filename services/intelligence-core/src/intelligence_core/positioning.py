from __future__ import annotations

from datetime import datetime
from decimal import Decimal, DivisionByZero
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator
from research_core.common import stable_hash

from intelligence_core.models import FrozenModel


class ParticipantType(StrEnum):
    FII = "FII"
    FPI = "FPI"
    DII = "DII"
    MUTUAL_FUND = "MUTUAL_FUND"
    INSURANCE = "INSURANCE"
    PROPRIETARY = "PROPRIETARY"
    RETAIL = "RETAIL"
    CLIENT = "CLIENT"
    FOREIGN_INSTITUTION = "FOREIGN_INSTITUTION"
    DOMESTIC_INSTITUTION = "DOMESTIC_INSTITUTION"
    UNKNOWN = "UNKNOWN"


class FlowType(StrEnum):
    CASH_MARKET = "CASH_MARKET"
    INDEX_FUTURES = "INDEX_FUTURES"
    STOCK_FUTURES = "STOCK_FUTURES"
    INDEX_OPTIONS = "INDEX_OPTIONS"
    STOCK_OPTIONS = "STOCK_OPTIONS"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    BLOCK_DEAL = "BLOCK_DEAL"
    BULK_DEAL = "BULK_DEAL"
    DELIVERY = "DELIVERY"
    OTHER = "OTHER"


class ActivityState(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class BasisState(StrEnum):
    PREMIUM = "PREMIUM"
    DISCOUNT = "DISCOUNT"
    NEAR_FAIR = "NEAR_FAIR"
    WIDENING = "WIDENING"
    NARROWING = "NARROWING"
    UNKNOWN = "UNKNOWN"


class PriceOIQuadrant(StrEnum):
    PRICE_UP_OI_UP = "PRICE_UP_OI_UP"
    PRICE_UP_OI_DOWN = "PRICE_UP_OI_DOWN"
    PRICE_DOWN_OI_UP = "PRICE_DOWN_OI_UP"
    PRICE_DOWN_OI_DOWN = "PRICE_DOWN_OI_DOWN"
    UNKNOWN = "UNKNOWN"


class OptionType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class ExpiryType(StrEnum):
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class SkewState(StrEnum):
    DOWNSIDE_RICH = "DOWNSIDE_RICH"
    UPSIDE_RICH = "UPSIDE_RICH"
    BALANCED = "BALANCED"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class CrowdingState(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class FlowObservation(FrozenModel):
    observation_id: UUID = Field(default_factory=uuid4)
    scope: str
    entity_id: str | None = None
    sector_id: str | None = None
    market_id: str | None = None
    flow_type: FlowType
    participant_type: ParticipantType
    buy_value: Decimal | None = None
    sell_value: Decimal | None = None
    net_value: Decimal | None = None
    gross_value: Decimal | None = None
    quantity: Decimal | None = None
    currency: str
    period_start: datetime
    period_end: datetime
    source_id: str
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    quality: str = "PASS"
    provenance: dict[str, Any]
    version: str = "1"
    payload_hash: str = ""

    @model_validator(mode="after")
    def validate_flow(self) -> FlowObservation:
        if self.period_start > self.period_end:
            raise ValueError("period_start must not follow period_end")
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("available_at must reflect publication and system observation")
        if (self.net_value is not None and self.buy_value is not None
                and self.sell_value is not None
                and self.net_value != self.buy_value - self.sell_value):
            raise ValueError("net_value must equal buy_value minus sell_value")
        if (self.gross_value is not None and self.buy_value is not None
                and self.sell_value is not None
                and self.gross_value != self.buy_value + self.sell_value):
            raise ValueError("gross_value must equal buy_value plus sell_value")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(
                self.model_dump(exclude={"payload_hash", "observation_id"}, mode="json")))
        return self


class InstitutionalFlowState(FrozenModel):
    foreign_cash_flow: Decimal | None
    domestic_cash_flow: Decimal | None
    foreign_derivatives_flow: Decimal | None
    net_institutional_flow: Decimal | None
    normalized_net_flow: Decimal | None
    flow_percentile: Decimal | None
    flow_zscore: Decimal | None
    flow_trend: str
    flow_acceleration: Decimal | None
    persistence: Decimal | None
    breadth: Decimal | None
    certainty: float = Field(ge=0, le=1)
    source_quality: str


class DeliveryObservation(FrozenModel):
    entity_id: str
    trading_date: datetime
    delivery_quantity: Decimal
    delivery_percentage: Decimal = Field(ge=0, le=100)
    traded_quantity: Decimal
    traded_value: Decimal
    turnover: Decimal
    source_id: str
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    quality: str = "PASS"

    @model_validator(mode="after")
    def validate_delivery(self) -> DeliveryObservation:
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("delivery observation is not causal")
        if self.delivery_quantity > self.traded_quantity:
            raise ValueError("delivery quantity exceeds traded quantity")
        return self


class DealObservation(FrozenModel):
    entity_id: str
    buyer: str | None = None
    seller: str | None = None
    quantity: Decimal
    value: Decimal | None = None
    price: Decimal | None = None
    deal_type: FlowType
    traded_at: datetime
    source_id: str
    available_at: datetime
    interpretation: str = "UNKNOWN_INTENT"

    @model_validator(mode="after")
    def validate_type(self) -> DealObservation:
        if self.deal_type not in {FlowType.BLOCK_DEAL, FlowType.BULK_DEAL}:
            raise ValueError("deal_type must be block or bulk deal")
        return self


class FuturesObservation(FrozenModel):
    instrument_id: str
    underlying: str
    contract_id: str
    expiry: datetime
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    settlement: Decimal | None = None
    volume: Decimal
    open_interest: Decimal
    change_in_open_interest: Decimal
    underlying_price: Decimal | None = None
    basis: Decimal | None = None
    annualized_basis: Decimal | None = None
    days_to_expiry: int = Field(ge=0)
    source_id: str
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    quality: str = "PASS"
    provenance: dict[str, Any]

    @model_validator(mode="after")
    def validate_futures(self) -> FuturesObservation:
        if self.expiry < self.timestamp:
            raise ValueError("expired futures observation")
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("futures available_at is not causal")
        expected_days = max(0, (self.expiry.date() - self.timestamp.date()).days)
        if self.days_to_expiry != expected_days:
            raise ValueError("days_to_expiry does not match exchange expiry metadata")
        expected_basis = self.close - self.underlying_price if self.underlying_price is not None else None
        if self.basis != expected_basis:
            raise ValueError("basis must equal futures close minus time-aligned spot")
        return self


class RolloverState(FrozenModel):
    underlying: str
    near_expiry: datetime
    next_expiry: datetime
    near_month_oi: Decimal
    next_month_oi: Decimal
    roll_activity: Decimal
    roll_percentage: Decimal | None
    roll_concentration: Decimal | None
    as_of: datetime
    interpretation: str = "POSITIONING_ACTIVITY_NOT_SENTIMENT"


class OptionObservation(FrozenModel):
    underlying: str
    contract_id: str
    expiry: datetime
    expiry_type: ExpiryType
    strike: Decimal
    option_type: OptionType
    timestamp: datetime
    bid: Decimal | None = None
    ask: Decimal | None = None
    last_price: Decimal | None = None
    volume: Decimal
    open_interest: Decimal
    change_in_open_interest: Decimal
    implied_volatility: Decimal | None = Field(default=None, ge=0)
    delta: Decimal | None = None
    gamma: Decimal | None = None
    vega: Decimal | None = None
    theta: Decimal | None = None
    underlying_price: Decimal | None = None
    moneyness: Decimal | None = None
    days_to_expiry: int = Field(ge=0)
    source_id: str
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    quality: str = "PASS"
    provenance: dict[str, Any]
    adjusted_contract: bool = False
    adjustment_reference: str | None = None

    @model_validator(mode="after")
    def validate_option(self) -> OptionObservation:
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("option available_at is not causal")
        if self.expiry < self.timestamp:
            raise ValueError("expired option observation")
        if self.days_to_expiry != (self.expiry.date() - self.timestamp.date()).days:
            raise ValueError("option days_to_expiry mismatch")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("bid exceeds ask")
        if self.adjusted_contract and not self.adjustment_reference:
            raise ValueError("adjusted derivative requires corporate-action reference")
        return self


class OptionChainSnapshot(FrozenModel):
    underlying: str
    expiry: datetime
    cutoff: datetime
    spot: Decimal | None
    strikes: tuple[Decimal, ...]
    calls: tuple[OptionObservation, ...]
    puts: tuple[OptionObservation, ...]
    aggregate_metrics: dict[str, Any]
    quality: str
    source_id: str
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def validate_chain(self) -> OptionChainSnapshot:
        options = (*self.calls, *self.puts)
        if any(x.available_at > self.cutoff for x in options):
            raise ValueError("option chain contains future evidence")
        if any(x.expiry != self.expiry or x.underlying != self.underlying for x in options):
            raise ValueError("option chain mixes expiry or underlying")
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class FlowSnapshot(FrozenModel):
    scope: str
    scope_id: str
    cutoff: datetime
    institutional_flows: tuple[FlowObservation, ...]
    deliveries: tuple[DeliveryObservation, ...]
    deals: tuple[DealObservation, ...]
    source_health: dict[str, str]
    quality: str
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def causal_hash(self) -> FlowSnapshot:
        if (any(x.available_at > self.cutoff for x in self.institutional_flows)
                or any(x.available_at > self.cutoff for x in self.deliveries)
                or any(x.available_at > self.cutoff for x in self.deals)):
            raise ValueError("flow snapshot contains future evidence")
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class DerivativesSnapshot(FrozenModel):
    underlying: str
    cutoff: datetime
    expiry_policy: str
    futures: tuple[FuturesObservation, ...]
    option_chains: tuple[OptionChainSnapshot, ...]
    basis_state: BasisState
    futures_oi_state: str
    options_oi_state: str
    iv_state: ActivityState
    skew_state: SkewState
    rollover_state: str
    crowding_state: CrowdingState
    expiry_context: dict[str, Any]
    quality: str
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def causal_hash(self) -> DerivativesSnapshot:
        if any(x.available_at > self.cutoff for x in self.futures):
            raise ValueError("derivatives snapshot contains future futures data")
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class FlowDerivativesEvidence(FrozenModel):
    engine_id: str = "flow-derivatives-evidence-engine"
    engine_version: str = "1"
    scope: str
    as_of: datetime
    horizon: str
    status: str
    institutional_flow_state: str
    delivery_state: ActivityState
    futures_oi_state: str
    basis_state: BasisState
    options_oi_state: str
    iv_state: ActivityState
    skew_state: SkewState
    rollover_state: str
    crowding_state: CrowdingState
    expiry_context: dict[str, Any]
    supporting_evidence: tuple[str, ...]
    adverse_evidence: tuple[str, ...]
    contradictions: tuple[str, ...]
    certainty: float = Field(ge=0, le=1)
    data_quality: str
    directional_evidence_score: Decimal | None = None
    explanation_payload: dict[str, Any]
    provenance: dict[str, Any]


def safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    try:
        return numerator / denominator if denominator else None
    except (DivisionByZero, ZeroDivisionError):
        return None


def normalize_flows(current: FlowObservation, history: list[FlowObservation]) -> dict[str, Decimal | None]:
    valid = [x for x in history if x.net_value is not None and x.gross_value is not None
             and x.currency == current.currency and x.flow_type == current.flow_type]
    if current.net_value is None or current.gross_value is None or len(valid) < 5:
        return {"normalized": None, "percentile": None, "zscore": None}
    gross_values = sorted(abs(x.gross_value or Decimal(0)) for x in valid)
    middle = len(gross_values) // 2
    gross_median = (gross_values[middle] if len(gross_values) % 2
                    else (gross_values[middle - 1] + gross_values[middle]) / Decimal(2))
    normalized = safe_ratio(current.net_value, gross_median)
    nets = [x.net_value for x in valid if x.net_value is not None]
    mean = sum(nets, Decimal(0)) / Decimal(len(nets))
    variance = sum((x - mean) ** 2 for x in nets) / Decimal(len(nets))
    std = variance.sqrt() if variance > 0 else Decimal(0)
    percentile = Decimal(sum(x <= current.net_value for x in nets)) / Decimal(len(nets))
    return {"normalized": normalized, "percentile": percentile,
            "zscore": safe_ratio(current.net_value - mean, std)}


def basis_state(current: FuturesObservation, prior: FuturesObservation | None = None) -> BasisState:
    if current.basis is None or current.underlying_price is None:
        return BasisState.UNKNOWN
    normalized = safe_ratio(current.basis, current.underlying_price)
    if prior and prior.basis is not None:
        if abs(current.basis) > abs(prior.basis) * Decimal("1.2"):
            return BasisState.WIDENING
        if abs(current.basis) < abs(prior.basis) * Decimal("0.8"):
            return BasisState.NARROWING
    if normalized is not None and abs(normalized) <= Decimal("0.001"):
        return BasisState.NEAR_FAIR
    return BasisState.PREMIUM if current.basis > 0 else BasisState.DISCOUNT


def price_oi_quadrant(current_price: Decimal | None, prior_price: Decimal | None,
                      oi_change: Decimal | None) -> PriceOIQuadrant:
    if current_price is None or prior_price is None or oi_change is None or current_price == prior_price:
        return PriceOIQuadrant.UNKNOWN
    if current_price > prior_price:
        return PriceOIQuadrant.PRICE_UP_OI_UP if oi_change > 0 else PriceOIQuadrant.PRICE_UP_OI_DOWN
    return PriceOIQuadrant.PRICE_DOWN_OI_UP if oi_change > 0 else PriceOIQuadrant.PRICE_DOWN_OI_DOWN


def pcr(options: list[OptionObservation], field: str) -> Decimal | None:
    if field not in {"volume", "open_interest", "change_in_open_interest"}:
        raise ValueError("unsupported PCR methodology")
    puts = sum((getattr(x, field) for x in options if x.option_type == OptionType.PUT), Decimal(0))
    calls = sum((getattr(x, field) for x in options if x.option_type == OptionType.CALL), Decimal(0))
    return safe_ratio(puts, calls)


def option_skew(options: list[OptionObservation]) -> tuple[Decimal | None, SkewState]:
    put_ivs = [x.implied_volatility for x in options
               if x.option_type == OptionType.PUT and x.implied_volatility is not None]
    call_ivs = [x.implied_volatility for x in options
                if x.option_type == OptionType.CALL and x.implied_volatility is not None]
    if not put_ivs or not call_ivs:
        return None, SkewState.UNKNOWN
    difference = (sum(put_ivs, Decimal(0)) / Decimal(len(put_ivs))
                  - sum(call_ivs, Decimal(0)) / Decimal(len(call_ivs)))
    state = (SkewState.EXTREME if abs(difference) >= Decimal(15) else
             SkewState.DOWNSIDE_RICH if difference >= Decimal(3) else
             SkewState.UPSIDE_RICH if difference <= Decimal(-3) else SkewState.BALANCED)
    return difference, state


def option_concentration(options: list[OptionObservation], *, top_n: int = 3) -> dict[str, Any]:
    calls = sorted((x for x in options if x.option_type == OptionType.CALL),
                   key=lambda x: x.open_interest, reverse=True)[:top_n]
    puts = sorted((x for x in options if x.option_type == OptionType.PUT),
                  key=lambda x: x.open_interest, reverse=True)[:top_n]
    total = sum((x.open_interest for x in options), Decimal(0))
    top = sum((x.open_interest for x in (*calls, *puts)), Decimal(0))
    return {"top_call_oi_strikes": tuple(x.strike for x in calls),
            "top_put_oi_strikes": tuple(x.strike for x in puts),
            "concentration": safe_ratio(top, total),
            "label": "POSITIONING_REFERENCE_NOT_PRICE_BARRIER"}


def build_option_chain(underlying: str, expiry: datetime, cutoff: datetime,
                       options: list[OptionObservation], *, spot: Decimal | None,
                       source_id: str) -> OptionChainSnapshot:
    known = [x for x in options if x.underlying == underlying and x.expiry == expiry
             and x.available_at <= cutoff]
    deduplicated = {x.contract_id: x for x in sorted(known, key=lambda x: x.available_at)}
    values = list(deduplicated.values())
    calls = tuple(x for x in values if x.option_type == OptionType.CALL)
    puts = tuple(x for x in values if x.option_type == OptionType.PUT)
    volume_pcr, oi_pcr, change_pcr = (pcr(values, x) for x in
                                      ("volume", "open_interest", "change_in_open_interest"))
    skew_value, skew = option_skew(values)
    strikes = tuple(sorted({x.strike for x in values}))
    complete = bool(calls and puts and spot is not None and len(strikes) >= 3)
    return OptionChainSnapshot(
        underlying=underlying, expiry=expiry, cutoff=cutoff, spot=spot, strikes=strikes,
        calls=calls, puts=puts,
        aggregate_metrics={"volume_pcr": volume_pcr, "oi_pcr": oi_pcr,
                           "change_in_oi_pcr": change_pcr, "pcr_interpretation": "STRUCTURE_ONLY",
                           "skew": skew_value, "skew_state": skew,
                           "concentration": option_concentration(values)},
        quality="PASS" if complete else "INCOMPLETE_CHAIN", source_id=source_id)


def build_flow_snapshot(scope: str, scope_id: str, cutoff: datetime,
                        flows: list[FlowObservation], *, deliveries: list[DeliveryObservation] | None = None,
                        deals: list[DealObservation] | None = None,
                        source_health: dict[str, str] | None = None) -> FlowSnapshot:
    def matches(item: FlowObservation) -> bool:
        return ((scope == "ENTITY" and item.entity_id == scope_id)
                or (scope == "SECTOR" and item.sector_id == scope_id)
                or (scope == "MARKET" and item.market_id == scope_id))
    known = tuple(x for x in flows if matches(x) and x.available_at <= cutoff)
    known_delivery = tuple(x for x in (deliveries or []) if x.entity_id == scope_id
                           and x.available_at <= cutoff) if scope == "ENTITY" else ()
    known_deals = tuple(x for x in (deals or []) if x.entity_id == scope_id
                        and x.available_at <= cutoff) if scope == "ENTITY" else ()
    return FlowSnapshot(scope=scope, scope_id=scope_id, cutoff=cutoff,
                        institutional_flows=known, deliveries=known_delivery, deals=known_deals,
                        source_health=source_health or {}, quality="PASS" if known else "INSUFFICIENT_DATA")


def build_derivatives_snapshot(underlying: str, cutoff: datetime, expiry_policy: str,
                               futures: list[FuturesObservation],
                               chains: list[OptionChainSnapshot]) -> DerivativesSnapshot:
    known_futures = tuple(x for x in futures if x.underlying == underlying and x.available_at <= cutoff)
    known_chains = tuple(x for x in chains if x.underlying == underlying and x.cutoff <= cutoff)
    latest = max(known_futures, key=lambda x: x.timestamp, default=None)
    latest_basis = basis_state(latest) if latest else BasisState.UNKNOWN
    all_options = [x for chain in known_chains for x in (*chain.calls, *chain.puts)]
    _, skew = option_skew(all_options)
    complete = bool(latest and known_chains and all(x.quality == "PASS" for x in known_chains))
    concentration = option_concentration(all_options).get("concentration") if all_options else None
    crowding = (CrowdingState.UNKNOWN if concentration is None else CrowdingState.EXTREME
                if concentration >= Decimal("0.8") else CrowdingState.ELEVATED
                if concentration >= Decimal("0.6") else CrowdingState.NORMAL)
    return DerivativesSnapshot(
        underlying=underlying, cutoff=cutoff, expiry_policy=expiry_policy,
        futures=known_futures, option_chains=known_chains, basis_state=latest_basis,
        futures_oi_state="UNKNOWN" if not latest else "OBSERVED_NOT_DIRECTION",
        options_oi_state="UNKNOWN" if not all_options else "OBSERVED_NOT_DIRECTION",
        iv_state=ActivityState.UNKNOWN if not any(x.implied_volatility is not None for x in all_options)
        else ActivityState.NORMAL, skew_state=skew, rollover_state="UNKNOWN",
        crowding_state=crowding,
        expiry_context={"policy": expiry_policy,
                        "days_to_expiry": latest.days_to_expiry if latest else None,
                        "dealer_gamma": "UNKNOWN"},
        quality="PASS" if complete else "INCOMPLETE_DERIVATIVES_DATA")


class FlowDerivativesEvidenceEngine:
    def evaluate(self, flow: FlowSnapshot, derivatives: DerivativesSnapshot | None,
                 *, horizon: str) -> FlowDerivativesEvidence:
        insufficient = not flow.institutional_flows or derivatives is None or derivatives.quality != "PASS"
        net = sum((x.net_value or Decimal(0) for x in flow.institutional_flows), Decimal(0))
        flow_state = "NET_INFLOW" if net > 0 else "NET_OUTFLOW" if net < 0 else "BALANCED_OR_UNKNOWN"
        contradictions: tuple[str, ...] = ()
        if derivatives and net > 0 and derivatives.skew_state == SkewState.DOWNSIDE_RICH:
            contradictions = ("institutional inflow coexists with downside-rich option skew",)
        return FlowDerivativesEvidence(
            scope=f"{flow.scope}:{flow.scope_id}", as_of=flow.cutoff, horizon=horizon,
            status="INSUFFICIENT_POSITIONING_EVIDENCE" if insufficient
            else "INTERNAL_POSITIONING_EVIDENCE_NOT_PREDICTION",
            institutional_flow_state=flow_state, delivery_state=ActivityState.UNKNOWN,
            futures_oi_state=derivatives.futures_oi_state if derivatives else "UNKNOWN",
            basis_state=derivatives.basis_state if derivatives else BasisState.UNKNOWN,
            options_oi_state=derivatives.options_oi_state if derivatives else "UNKNOWN",
            iv_state=derivatives.iv_state if derivatives else ActivityState.UNKNOWN,
            skew_state=derivatives.skew_state if derivatives else SkewState.UNKNOWN,
            rollover_state=derivatives.rollover_state if derivatives else "UNKNOWN",
            crowding_state=derivatives.crowding_state if derivatives else CrowdingState.UNKNOWN,
            expiry_context=derivatives.expiry_context if derivatives else {"status": "UNKNOWN"},
            supporting_evidence=tuple(str(x.observation_id) for x in flow.institutional_flows
                                      if (x.net_value or 0) > 0),
            adverse_evidence=tuple(str(x.observation_id) for x in flow.institutional_flows
                                   if (x.net_value or 0) < 0),
            contradictions=contradictions, certainty=0 if insufficient else 0.6,
            data_quality="INSUFFICIENT" if insufficient else "FIXTURE_PASS",
            directional_evidence_score=None,
            explanation_payload={"label": "INTERNAL POSITIONING INTELLIGENCE — NOT PREDICTION",
                                 "ambiguity": ["hedging", "market making", "structured exposure"],
                                 "not": ["price probability", "expected return", "buy/sell"]},
            provenance={"flow_snapshot": flow.snapshot_hash,
                        "derivatives_snapshot": derivatives.snapshot_hash if derivatives else None})


def positioning_qa(flow: FlowSnapshot, derivatives: DerivativesSnapshot | None) -> dict[str, Any]:
    chains = derivatives.option_chains if derivatives else ()
    options = [x for chain in chains for x in (*chain.calls, *chain.puts)]
    return {
        "flow_freshness": "UNKNOWN" if not flow.institutional_flows else "AVAILABLE_BY_CUTOFF",
        "flow_completeness": len(flow.institutional_flows),
        "oi_freshness": "UNKNOWN" if not derivatives or not derivatives.futures else "AVAILABLE_BY_CUTOFF",
        "chain_completeness": sum(x.quality == "PASS" for x in chains) / max(1, len(chains)),
        "strike_coverage": len({x.strike for x in options}),
        "expiry_coverage": len({x.expiry for x in options}),
        "iv_availability": sum(x.implied_volatility is not None for x in options) / max(1, len(options)),
        "participant_coverage": len({x.participant_type for x in flow.institutional_flows}),
        "abstention": not flow.institutional_flows or not derivatives or derivatives.quality != "PASS",
    }
