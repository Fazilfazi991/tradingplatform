from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True)
    available_at: datetime
    source_id: str
    quality: str
    provenance: dict[str, Any]


class NewsObservation(Contract):
    headline: str
    entity_ids: tuple[str, ...]
    event_type: str
    sentiment: str = "UNKNOWN"
    novelty: str
    certainty: float


class FundamentalObservation(Contract):
    entity_id: str
    metric: Literal[
        "REVENUE",
        "PROFIT",
        "EPS",
        "MARGIN",
        "DEBT",
        "CASH_FLOW",
        "ROE",
        "ROCE",
        "VALUATION",
        "GUIDANCE",
        "REVISION",
        "SURPRISE",
    ]
    value: float | None
    period: str


class MacroObservation(Contract):
    series: str
    period: str
    original_value: float
    release_time: datetime
    revision_value: float | None = None
    revision_available_at: datetime | None = None

    def value_as_of(self, cutoff: datetime) -> float:
        if (
            self.revision_value is not None
            and self.revision_available_at
            and self.revision_available_at <= cutoff
        ):
            return self.revision_value
        return self.original_value


class FlowObservation(Contract):
    flow_type: str
    value: float | None
    entity_id: str | None = None


class DerivativesObservation(Contract):
    instrument_id: str
    metric: str
    value: float | None
    expiry: datetime | None = None


class PsychologyObservation(Contract):
    measure: str
    value: float | None
    entity_id: str | None = None


class CrossMarketObservation(Contract):
    instrument: str
    metric: str
    value: float | None


class IntelligenceFeatureValue(Contract):
    feature_id: str
    version: str
    entity_id: str
    value: float | None
    input_sources: tuple[str, ...]


class LLMAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str
    model: str
    model_version: str
    template_version: str
    input_hash: str
    output_hash: str
    timestamp: datetime
    classification: str
    evidence_spans: tuple[str, ...]
    validation_state: str
    review_state: str
    provenance: Literal["DERIVED"] = "DERIVED"


class FixtureLLMAnalyzer:
    def analyze(self, text: str, *, now: datetime) -> LLMAnalysis:
        from research_core.common import stable_hash

        classification = "EARNINGS" if "earnings" in text.lower() else "UNKNOWN"
        spans = ("earnings",) if classification == "EARNINGS" else ()
        payload = {"classification": classification, "spans": spans}
        return LLMAnalysis(
            provider="FIXTURE",
            model="DETERMINISTIC_RULES",
            model_version="1",
            template_version="1",
            input_hash=stable_hash(text),
            output_hash=stable_hash(payload),
            timestamp=now,
            classification=classification,
            evidence_spans=spans,
            validation_state="VALID" if spans else "INSUFFICIENT_EVIDENCE",
            review_state="UNREVIEWED",
        )
