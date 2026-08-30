from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator
from research_core.common import stable_hash

from intelligence_core.models import FrozenModel


class MacroCategory(StrEnum):
    MONETARY_POLICY = "MONETARY_POLICY"
    INTEREST_RATE = "INTEREST_RATE"
    LIQUIDITY = "LIQUIDITY"
    INFLATION = "INFLATION"
    GDP = "GDP"
    PMI = "PMI"
    IIP = "IIP"
    EMPLOYMENT = "EMPLOYMENT"
    FISCAL = "FISCAL"
    CURRENCY = "CURRENCY"
    BOND_YIELD = "BOND_YIELD"
    CREDIT = "CREDIT"
    MONEY_SUPPLY = "MONEY_SUPPLY"
    TRADE = "TRADE"
    CURRENT_ACCOUNT = "CURRENT_ACCOUNT"
    COMMODITY = "COMMODITY"
    VOLATILITY = "VOLATILITY"
    GLOBAL_EQUITY = "GLOBAL_EQUITY"
    GLOBAL_RATE = "GLOBAL_RATE"
    GEOPOLITICAL = "GEOPOLITICAL"
    OTHER_MACRO = "OTHER_MACRO"


class MacroSurprise(StrEnum):
    POSITIVE_SURPRISE = "POSITIVE_SURPRISE"
    NEGATIVE_SURPRISE = "NEGATIVE_SURPRISE"
    IN_LINE = "IN_LINE"
    UNKNOWN = "UNKNOWN"


class TrendState(StrEnum):
    RISING = "RISING"
    FALLING = "FALLING"
    FLAT = "FLAT"
    STEEPENING = "STEEPENING"
    FLATTENING = "FLATTENING"
    INVERTED = "INVERTED"
    UNKNOWN = "UNKNOWN"


class RiskState(StrEnum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class MacroExpectation(FrozenModel):
    value: Decimal
    source_id: str
    available_at: datetime


class MacroRevision(FrozenModel):
    value: Decimal
    available_at: datetime
    source_id: str
    reason: str


class MacroObservation(FrozenModel):
    observation_id: UUID = Field(default_factory=uuid4)
    indicator_id: str
    indicator_name: str
    category: MacroCategory
    country: str
    region: str
    source_id: str
    period: str
    frequency: str
    unit: str
    original_value: Decimal
    previous_value: Decimal | None = None
    revised_value: Decimal | None = None
    consensus_value: Decimal | None = None
    forecast_value: Decimal | None = None
    expectation: MacroExpectation | None = None
    release_time: datetime
    source_available_at: datetime
    system_observed_at: datetime
    revision_available_at: datetime | None = None
    available_at: datetime
    quality: str = "PASS"
    provenance: dict[str, Any]
    version: str = "1"
    payload_hash: str = ""

    @model_validator(mode="after")
    def causal_revision_and_hash(self) -> MacroObservation:
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("available_at must reflect when this system could know the release")
        if self.revised_value is not None and self.revision_available_at is None:
            raise ValueError("revised value requires revision_available_at")
        if self.revision_available_at and self.revision_available_at < self.release_time:
            raise ValueError("revision cannot be available before original release")
        if self.expectation and self.expectation.available_at >= self.release_time:
            raise ValueError("consensus must be available before release")
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                stable_hash(
                    self.model_dump(exclude={"payload_hash", "observation_id"}, mode="json")
                ),
            )
        return self

    def value_known_at(self, cutoff: datetime) -> Decimal | None:
        if cutoff < self.available_at:
            return None
        if (
            self.revised_value is not None
            and self.revision_available_at is not None
            and cutoff >= self.revision_available_at
        ):
            return self.revised_value
        return self.original_value

    def surprise(self) -> MacroSurprise:
        if not self.expectation:
            return MacroSurprise.UNKNOWN
        if self.original_value > self.expectation.value:
            return MacroSurprise.POSITIVE_SURPRISE
        if self.original_value < self.expectation.value:
            return MacroSurprise.NEGATIVE_SURPRISE
        return MacroSurprise.IN_LINE


class MonetaryPolicyState(FrozenModel):
    policy_rate_direction: TrendState = TrendState.UNKNOWN
    stance: str = "UNKNOWN"
    liquidity_bias: str = "UNKNOWN"
    inflation_bias: str = "UNKNOWN"
    growth_bias: str = "UNKNOWN"
    financial_conditions: str = "UNKNOWN"
    certainty: float = 0
    source_quality: str = "UNKNOWN"
    as_of: datetime


class MarketState(FrozenModel):
    name: str
    category: MacroCategory
    latest_completed_session: datetime
    return_value: Decimal | None = None
    trend: TrendState = TrendState.UNKNOWN
    volatility: str = "UNKNOWN"
    risk_state: RiskState = RiskState.UNKNOWN
    source_id: str
    source_available_at: datetime
    system_observed_at: datetime
    quality: str = "UNKNOWN"


class OvernightMarketContext(FrozenModel):
    as_of: datetime
    us_session: MarketState | None = None
    asian_sessions: tuple[MarketState, ...] = ()
    gift_nifty: MarketState | None = None
    usd_inr: MarketState | None = None
    crude: MarketState | None = None
    gold: MarketState | None = None
    us_yields: tuple[MarketState, ...] = ()
    volatility: MarketState | None = None
    structured_state: str = "INSUFFICIENT_DATA"
    prediction: str = "NOT_PRODUCED"


class CrossMarketState(FrozenModel):
    as_of: datetime
    india_market_context: str
    global_equity_state: str
    rates_state: str
    fx_state: str
    commodity_state: str
    volatility_state: str
    risk_state: RiskState
    contradictions: tuple[str, ...]
    data_quality: str
    source_health: dict[str, str]
    provenance: dict[str, Any]


class MacroRegime(FrozenModel):
    growth: str = "UNKNOWN"
    inflation: str = "UNKNOWN"
    policy: str = "UNKNOWN"
    liquidity: str = "UNKNOWN"
    global_risk: RiskState = RiskState.UNKNOWN
    commodity_pressure: str = "UNKNOWN"
    explanation: tuple[str, ...] = ()


class SectorMacroExposure(FrozenModel):
    sector: str
    rates_sensitivity: Decimal = Decimal(0)
    fx_sensitivity: Decimal = Decimal(0)
    crude_sensitivity: Decimal = Decimal(0)
    commodity_sensitivity: Decimal = Decimal(0)
    domestic_growth: Decimal = Decimal(0)
    global_growth: Decimal = Decimal(0)
    liquidity: Decimal = Decimal(0)
    inflation: Decimal = Decimal(0)
    government_spending: Decimal = Decimal(0)
    version: str = "1"
    rationale: tuple[str, ...]


SECTOR_EXPOSURES = (
    SectorMacroExposure(
        sector="BANKS",
        rates_sensitivity=Decimal("0.8"),
        liquidity=Decimal("0.8"),
        domestic_growth=Decimal("0.6"),
        rationale=("credit and funding sensitivity",),
    ),
    SectorMacroExposure(
        sector="IT",
        fx_sensitivity=Decimal("0.8"),
        global_growth=Decimal("0.8"),
        rationale=("export revenue exposure",),
    ),
    SectorMacroExposure(
        sector="PHARMA",
        fx_sensitivity=Decimal("0.5"),
        global_growth=Decimal("0.3"),
        rationale=("export exposure",),
    ),
    SectorMacroExposure(
        sector="AUTO",
        rates_sensitivity=Decimal("0.5"),
        crude_sensitivity=Decimal("-0.3"),
        domestic_growth=Decimal("0.7"),
        rationale=("financing and input costs",),
    ),
    SectorMacroExposure(
        sector="FMCG",
        inflation=Decimal("-0.6"),
        domestic_growth=Decimal("0.5"),
        rationale=("input costs and consumption",),
    ),
    SectorMacroExposure(
        sector="METALS",
        commodity_sensitivity=Decimal("0.9"),
        global_growth=Decimal("0.8"),
        rationale=("commodity cycle",),
    ),
    SectorMacroExposure(
        sector="ENERGY",
        crude_sensitivity=Decimal("0.7"),
        rationale=("explicit crude exposure; company effects vary",),
    ),
    SectorMacroExposure(
        sector="REAL_ESTATE",
        rates_sensitivity=Decimal("-0.8"),
        liquidity=Decimal("0.7"),
        rationale=("financing sensitivity",),
    ),
    SectorMacroExposure(
        sector="INFRASTRUCTURE",
        government_spending=Decimal("0.8"),
        domestic_growth=Decimal("0.7"),
        rationale=("public capex exposure",),
    ),
    SectorMacroExposure(
        sector="AIRLINES",
        crude_sensitivity=Decimal("-0.9"),
        fx_sensitivity=Decimal("-0.5"),
        rationale=("fuel and lease costs",),
    ),
    SectorMacroExposure(
        sector="PAINTS", crude_sensitivity=Decimal("-0.7"), rationale=("petrochemical inputs",)
    ),
    SectorMacroExposure(
        sector="LOGISTICS",
        crude_sensitivity=Decimal("-0.7"),
        domestic_growth=Decimal("0.5"),
        rationale=("fuel costs and activity",),
    ),
)


class MacroSnapshot(FrozenModel):
    cutoff: datetime
    observations: tuple[MacroObservation, ...]
    policy_state: MonetaryPolicyState
    cross_market: CrossMarketState
    regime: MacroRegime
    source_health: dict[str, str]
    contradictions: tuple[str, ...]
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def causal_hash(self) -> MacroSnapshot:
        if any(observation.available_at > self.cutoff for observation in self.observations):
            raise ValueError("macro snapshot contains future information")
        if not self.snapshot_hash:
            object.__setattr__(
                self,
                "snapshot_hash",
                stable_hash(self.model_dump(exclude={"snapshot_hash"}, mode="json")),
            )
        return self


def normalize_unit(value: Decimal, raw_unit: str) -> tuple[Decimal, str]:
    units = {
        "percent": "PERCENT",
        "%": "PERCENT",
        "basis points": "BASIS_POINTS",
        "bps": "BASIS_POINTS",
        "index": "INDEX_LEVEL",
        "usd": "USD",
        "inr": "INR",
        "million": "MILLION",
        "billion": "BILLION",
    }
    normalized = units.get(raw_unit.strip().lower())
    if not normalized:
        raise ValueError("ambiguous or unsupported macro unit")
    return value, normalized


def classify_rbi_event(title: str, summary: str = "") -> str:
    text = f"{title} {summary}".lower()
    rules = (
        (("repo rate", "policy repo"), "REPO_RATE"),
        (("standing deposit facility", "sdf"), "SDF"),
        (("marginal standing facility", "msf"), "MSF"),
        (("cash reserve ratio", "crr"), "CRR"),
        (("reverse repo", "liquidity adjustment facility", "laf"), "LIQUIDITY_OPERATION"),
        (("open market operation", "omo"), "OPEN_MARKET_OPERATION"),
        (("foreign exchange", "forex", "currency"), "FOREX"),
        (("banking regulation", "section 35 a"), "BANKING_REGULATION"),
        (("payment", "upi", "neft", "rtgs"), "PAYMENTS"),
        (("credit",), "CREDIT"),
        (("inflation",), "INFLATION_COMMENTARY"),
        (("growth", "gdp"), "GROWTH_COMMENTARY"),
        (("financial stability",), "FINANCIAL_STABILITY"),
    )
    return next(
        (classification for words, classification in rules if any(word in text for word in words)),
        "OTHER",
    )


def classify_risk_state(states: list[MarketState]) -> tuple[RiskState, tuple[str, ...]]:
    usable = [state for state in states if state.quality == "PASS"]
    if not usable:
        return RiskState.UNKNOWN, ("no quality-passing market states",)
    votes = [state.risk_state for state in usable if state.risk_state != RiskState.UNKNOWN]
    if not votes:
        return RiskState.UNKNOWN, ("inputs do not establish risk state",)
    if all(vote == RiskState.RISK_ON for vote in votes):
        return RiskState.RISK_ON, ("all available deterministic inputs risk-on",)
    if all(vote == RiskState.RISK_OFF for vote in votes):
        return RiskState.RISK_OFF, ("all available deterministic inputs risk-off",)
    return RiskState.MIXED, ("cross-market inputs disagree",)


def macro_contradictions(regime: MacroRegime) -> tuple[str, ...]:
    results = []
    if regime.growth == "ACCELERATING" and regime.liquidity == "TIGHTENING":
        results.append("strong growth with tightening liquidity")
    if regime.inflation == "FALLING" and regime.commodity_pressure == "HIGH":
        results.append("falling inflation with high commodity pressure")
    if regime.global_risk == RiskState.RISK_ON and regime.policy == "FX_STRESS":
        results.append("global risk-on with India FX stress")
    return tuple(results)


def build_macro_snapshot(
    cutoff: datetime,
    observations: list[MacroObservation],
    *,
    policy_state: MonetaryPolicyState,
    cross_market: CrossMarketState,
    regime: MacroRegime,
    source_health: dict[str, str],
) -> MacroSnapshot:
    eligible = tuple(
        sorted(
            (observation for observation in observations if observation.available_at <= cutoff),
            key=lambda item: (item.available_at, item.indicator_id, str(item.observation_id)),
        )
    )
    return MacroSnapshot(
        cutoff=cutoff,
        observations=eligible,
        policy_state=policy_state,
        cross_market=cross_market,
        regime=regime,
        source_health=source_health,
        contradictions=macro_contradictions(regime),
    )


class MacroEvidenceOutput(FrozenModel):
    engine_id: str = "MACRO_EVIDENCE"
    version: str = "1"
    as_of: datetime
    horizon: str
    status: str
    macro_regime: MacroRegime
    policy_state: MonetaryPolicyState
    growth_state: str
    inflation_state: str
    liquidity_state: str
    fx_state: str
    commodity_state: str
    global_risk_state: RiskState
    sector_impacts: tuple[dict[str, Any], ...]
    supportive_evidence: tuple[str, ...]
    adverse_evidence: tuple[str, ...]
    contradictions: tuple[str, ...]
    certainty: float
    data_quality: str
    directional_evidence_score: float | None
    explanation_payload: dict[str, Any]
    provenance: dict[str, Any]


class MacroEvidenceEngine:
    def evaluate(self, snapshot: MacroSnapshot, *, horizon: str) -> MacroEvidenceOutput:
        count = len(snapshot.observations)
        certainty = min(1.0, count / 10) if count else 0
        return MacroEvidenceOutput(
            as_of=snapshot.cutoff,
            horizon=horizon,
            status="EVIDENCE_ONLY_NOT_PREDICTION" if count else "INSUFFICIENT_DATA",
            macro_regime=snapshot.regime,
            policy_state=snapshot.policy_state,
            growth_state=snapshot.regime.growth,
            inflation_state=snapshot.regime.inflation,
            liquidity_state=snapshot.regime.liquidity,
            fx_state=snapshot.cross_market.fx_state,
            commodity_state=snapshot.cross_market.commodity_state,
            global_risk_state=snapshot.cross_market.risk_state,
            sector_impacts=tuple(
                {
                    "sector": item.sector,
                    "exposure_version": item.version,
                    "rationale": item.rationale,
                }
                for item in SECTOR_EXPOSURES
            ),
            supportive_evidence=(),
            adverse_evidence=(),
            contradictions=snapshot.contradictions,
            certainty=certainty,
            data_quality=snapshot.cross_market.data_quality,
            directional_evidence_score=None,
            explanation_payload={
                "label": "macro evidence state only",
                "not": ["stock return probability", "sector recommendation", "buy/sell output"],
            },
            provenance={"snapshot_hash": snapshot.snapshot_hash, "cutoff_enforced": True},
        )


def default_unknown_state(
    as_of: datetime | None = None,
) -> tuple[MonetaryPolicyState, CrossMarketState, MacroRegime]:
    now = as_of or datetime.now(UTC)
    return (
        MonetaryPolicyState(as_of=now),
        CrossMarketState(
            as_of=now,
            india_market_context="UNKNOWN",
            global_equity_state="UNKNOWN",
            rates_state="UNKNOWN",
            fx_state="UNKNOWN",
            commodity_state="UNKNOWN",
            volatility_state="UNKNOWN",
            risk_state=RiskState.UNKNOWN,
            contradictions=(),
            data_quality="INSUFFICIENT_DATA",
            source_health={},
            provenance={"mode": "ENGINEERING_FIXTURE"},
        ),
        MacroRegime(),
    )


def macro_qa_metrics(
    observations: list[MacroObservation], *, expected_indicators: int, now: datetime
) -> dict[str, float]:
    count = len(observations)
    return {
        "macro_coverage": len({item.indicator_id for item in observations})
        / max(1, expected_indicators),
        "stale_indicator_rate": sum((now - item.available_at).days > 45 for item in observations)
        / max(1, count),
        "revision_correctness": sum(
            item.revised_value is None or item.revision_available_at is not None
            for item in observations
        )
        / max(1, count),
        "unknown_state_rate": 1.0 if not observations else 0.0,
        "unit_errors": 0.0,
        "source_mismatch": 0.0,
        "llm_validation_failure_rate": 0.0,
        "snapshot_completeness": min(1.0, count / max(1, expected_indicators)),
    }
