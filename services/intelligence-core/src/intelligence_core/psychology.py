from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from enum import StrEnum
from math import sqrt
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator
from research_core.common import stable_hash

from intelligence_core.models import FrozenModel


class SentimentType(StrEnum):
    NEWS_SENTIMENT = "NEWS_SENTIMENT"
    EVENT_SENTIMENT = "EVENT_SENTIMENT"
    MANAGEMENT_TONE = "MANAGEMENT_TONE"
    ANALYST_TONE = "ANALYST_TONE"
    REGULATORY_TONE = "REGULATORY_TONE"
    MACRO_TONE = "MACRO_TONE"
    SOCIAL_SENTIMENT = "SOCIAL_SENTIMENT"
    ATTENTION_SENTIMENT = "ATTENTION_SENTIMENT"
    MARKET_REACTION_SENTIMENT = "MARKET_REACTION_SENTIMENT"
    OTHER = "OTHER"


class SentimentDirection(StrEnum):
    STRONGLY_POSITIVE = "STRONGLY_POSITIVE"
    POSITIVE = "POSITIVE"
    SLIGHTLY_POSITIVE = "SLIGHTLY_POSITIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    SLIGHTLY_NEGATIVE = "SLIGHTLY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    STRONGLY_NEGATIVE = "STRONGLY_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class NarrativeLifecycle(StrEnum):
    EMERGING = "EMERGING"
    ACCELERATING = "ACCELERATING"
    ESTABLISHED = "ESTABLISHED"
    SATURATED = "SATURATED"
    WEAKENING = "WEAKENING"
    REVERSING = "REVERSING"
    DORMANT = "DORMANT"
    UNKNOWN = "UNKNOWN"


class IntensityState(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class DisagreementState(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class CrowdingState(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


DIRECTION_SCORE = {
    SentimentDirection.STRONGLY_POSITIVE: 1.0,
    SentimentDirection.POSITIVE: 0.65,
    SentimentDirection.SLIGHTLY_POSITIVE: 0.3,
    SentimentDirection.NEUTRAL: 0.0,
    SentimentDirection.MIXED: 0.0,
    SentimentDirection.SLIGHTLY_NEGATIVE: -0.3,
    SentimentDirection.NEGATIVE: -0.65,
    SentimentDirection.STRONGLY_NEGATIVE: -1.0,
    SentimentDirection.UNKNOWN: 0.0,
}


class SentimentObservation(FrozenModel):
    observation_id: UUID = Field(default_factory=uuid4)
    entity_id: str | None = None
    sector_id: str | None = None
    market_id: str | None = None
    source_id: str
    source_type: str
    content_reference: str
    event_id: str | None = None
    cluster_id: str
    sentiment_type: SentimentType
    sentiment_direction: SentimentDirection
    sentiment_strength: float = Field(ge=0, le=1)
    certainty: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    source_reliability: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    confirmation_state: str
    attention_weight: float = Field(ge=0)
    published_at: datetime
    source_available_at: datetime
    system_observed_at: datetime
    available_at: datetime
    analyzer: str
    analyzer_version: str
    evidence_refs: tuple[str, ...]
    payload_hash: str = ""
    status: str = "DERIVED_INTERPRETATION"
    is_rumour: bool = False

    @model_validator(mode="after")
    def causal_hash(self) -> SentimentObservation:
        if not any((self.entity_id, self.sector_id, self.market_id)):
            raise ValueError("at least one sentiment scope is required")
        if self.available_at != max(self.source_available_at, self.system_observed_at):
            raise ValueError("available_at must reflect when sentiment could be known")
        if not self.evidence_refs:
            raise ValueError("sentiment requires evidence references")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(
                self.model_dump(exclude={"payload_hash", "observation_id"}, mode="json")))
        return self


class PsychologyObservation(FrozenModel):
    attention: float = Field(ge=0, le=1)
    fear: float = Field(ge=0, le=1)
    euphoria: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)
    disagreement: float = Field(ge=0, le=1)
    crowding: float = Field(ge=0, le=1)
    speculative_intensity: float = Field(ge=0, le=1)
    narrative_strength: float = Field(ge=0, le=1)
    narrative_velocity: float
    narrative_persistence: float = Field(ge=0, le=1)
    narrative_reversal: float = Field(ge=0, le=1)
    source_diversity: float = Field(ge=0, le=1)
    information_density: float = Field(ge=0)
    as_of: datetime
    quality: str
    provenance: dict[str, Any]


class AttentionMetrics(FrozenModel):
    mentions_1h: int
    mentions_6h: int
    mentions_1d: int
    mentions_5d: int
    unique_sources: int
    unique_clusters: int
    novel_events: int
    attention_zscore: float
    attention_percentile: float = Field(ge=0, le=100)
    attention_velocity: float
    attention_acceleration: float
    material_event_velocity: float
    headline_velocity: float
    source_diversity: float = Field(ge=0, le=1)
    duplicate_suppression_rate: float = Field(ge=0, le=1)


class Narrative(FrozenModel):
    narrative_id: str
    entity_id: str | None = None
    sector_id: str | None = None
    market_id: str | None = None
    topic: str
    summary: str
    first_seen: datetime
    last_seen: datetime
    current_strength: float = Field(ge=0, le=1)
    velocity: float
    persistence: float = Field(ge=0, le=1)
    confirmation: str
    source_diversity: float = Field(ge=0, le=1)
    sentiment: SentimentDirection
    supporting_events: tuple[str, ...]
    contradicting_events: tuple[str, ...] = ()
    status: NarrativeLifecycle
    provenance: dict[str, Any]
    parent_narrative_id: str | None = None

    @model_validator(mode="after")
    def require_support(self) -> Narrative:
        if not self.supporting_events:
            raise ValueError("narrative labels require supporting evidence")
        if self.last_seen < self.first_seen:
            raise ValueError("narrative last_seen precedes first_seen")
        return self


class ScopeSentimentState(FrozenModel):
    scope: str
    scope_id: str
    as_of: datetime
    current_sentiment: SentimentDirection
    sentiment_trend: str
    attention: AttentionMetrics
    disagreement: DisagreementState
    dominant_narratives: tuple[Narrative, ...]
    material_events: tuple[str, ...]
    rumour_burden: float = Field(ge=0, le=1)
    certainty: float = Field(ge=0, le=1)
    source_quality: str
    breadth: dict[str, float] = Field(default_factory=dict)
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def set_hash(self) -> ScopeSentimentState:
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class PsychologySnapshot(FrozenModel):
    cutoff: datetime
    scope: str
    scope_id: str
    observations: tuple[SentimentObservation, ...]
    sentiment: ScopeSentimentState
    psychology: PsychologyObservation
    narratives: tuple[Narrative, ...]
    fear_state: IntensityState
    euphoria_state: IntensityState
    uncertainty_state: IntensityState
    crowding_state: CrowdingState
    speculative_state: IntensityState
    source_quality: str
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def causal_hash(self) -> PsychologySnapshot:
        if any(item.available_at > self.cutoff for item in self.observations):
            raise ValueError("psychology snapshot contains future evidence")
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(
                self.model_dump(exclude={"snapshot_hash"}, mode="json")))
        return self


class PsychologyEvidence(FrozenModel):
    engine_id: str = "psychology-evidence-engine"
    engine_version: str = "1"
    as_of: datetime
    scope: str
    horizon: str
    status: str
    sentiment_state: SentimentDirection
    attention_state: IntensityState
    fear_state: IntensityState
    euphoria_state: IntensityState
    uncertainty_state: IntensityState
    disagreement_state: DisagreementState
    crowding_state: CrowdingState
    speculative_state: IntensityState
    dominant_narratives: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    certainty: float = Field(ge=0, le=1)
    data_quality: str
    directional_evidence_score: float | None = None
    explanation_payload: dict[str, Any]
    provenance: dict[str, Any]


TIME_DECAY_METADATA = {
    "RUMOUR": {"relative_decay": "FAST", "half_life_hours": None, "optimized": False},
    "MAJOR_CORPORATE_EVENT": {"relative_decay": "SLOWER", "half_life_hours": None,
                              "optimized": False},
    "MACRO_POLICY_NARRATIVE": {"relative_decay": "LONGER", "half_life_hours": None,
                               "optimized": False},
}


def attention_metrics(records: list[SentimentObservation], cutoff: datetime) -> AttentionMetrics:
    eligible = [x for x in records if x.available_at <= cutoff and cutoff - x.available_at <= timedelta(days=5)]
    def clusters(hours: int) -> set[str]:
        return {x.cluster_id for x in eligible if cutoff - x.available_at <= timedelta(hours=hours)}
    c1, c6, c24, c120 = (clusters(x) for x in (1, 6, 24, 120))
    sources = {x.source_id for x in eligible}
    total = len(eligible)
    unique = len(c120)
    current_rate = len(c6) / 6
    previous = {x.cluster_id for x in eligible
                if timedelta(hours=6) < cutoff - x.available_at <= timedelta(hours=12)}
    prior_rate = len(previous) / 6
    velocity = current_rate - prior_rate
    older = {x.cluster_id for x in eligible
             if timedelta(hours=12) < cutoff - x.available_at <= timedelta(hours=18)}
    acceleration = velocity - (prior_rate - len(older) / 6)
    baseline = max(1.0, len(c120) / 5)
    zscore = (len(c24) - baseline) / sqrt(baseline)
    return AttentionMetrics(
        mentions_1h=len(c1), mentions_6h=len(c6), mentions_1d=len(c24), mentions_5d=unique,
        unique_sources=len(sources), unique_clusters=unique,
        novel_events=sum(x.novelty >= 0.8 for x in _unique_clusters(eligible)),
        attention_zscore=zscore, attention_percentile=min(100, max(0, 50 + zscore * 15)),
        attention_velocity=velocity, attention_acceleration=acceleration,
        material_event_velocity=sum(x.sentiment_strength >= 0.75 for x in _unique_clusters(eligible)) / 5,
        headline_velocity=current_rate, source_diversity=min(1, len(sources) / max(1, unique)),
        duplicate_suppression_rate=(total - unique) / max(1, total),
    )


def _unique_clusters(records: list[SentimentObservation]) -> list[SentimentObservation]:
    best: dict[str, SentimentObservation] = {}
    for item in sorted(records, key=lambda x: (x.available_at, str(x.observation_id))):
        if item.cluster_id not in best or item.source_reliability > best[item.cluster_id].source_reliability:
            best[item.cluster_id] = item
    return list(best.values())


def aggregate_sentiment(records: list[SentimentObservation]) -> tuple[SentimentDirection, float, float]:
    clusters = _unique_clusters(records)
    if not clusters:
        return SentimentDirection.UNKNOWN, 0, 1
    weighted = []
    for item in clusters:
        confirmation = 0.2 if item.is_rumour else 1.0 if "CONFIRMED" in item.confirmation_state else 0.65
        weight = (item.sentiment_strength * item.certainty * item.relevance
                  * item.source_reliability * item.novelty * confirmation)
        weighted.append((DIRECTION_SCORE[item.sentiment_direction], weight))
    total = sum(weight for _, weight in weighted)
    if total <= 0:
        return SentimentDirection.UNKNOWN, 0, 1
    score = sum(value * weight for value, weight in weighted) / total
    disagreement = min(1.0, sum(weight * abs(value - score) for value, weight in weighted) / total)
    direction = (SentimentDirection.STRONGLY_POSITIVE if score >= 0.8 else
                 SentimentDirection.POSITIVE if score >= 0.45 else
                 SentimentDirection.SLIGHTLY_POSITIVE if score >= 0.15 else
                 SentimentDirection.STRONGLY_NEGATIVE if score <= -0.8 else
                 SentimentDirection.NEGATIVE if score <= -0.45 else
                 SentimentDirection.SLIGHTLY_NEGATIVE if score <= -0.15 else
                 SentimentDirection.MIXED if disagreement >= 0.3 else SentimentDirection.NEUTRAL)
    return direction, score, disagreement


def classify_disagreement(value: float, count: int) -> DisagreementState:
    if count < 2:
        return DisagreementState.UNKNOWN
    return (DisagreementState.EXTREME if value >= 0.65 else DisagreementState.HIGH if value >= 0.4
            else DisagreementState.MEDIUM if value >= 0.2 else DisagreementState.LOW)


def classify_intensity(value: float, inputs: int) -> IntensityState:
    if inputs < 2:
        return IntensityState.UNKNOWN
    return (IntensityState.EXTREME if value >= 0.85 else IntensityState.HIGH if value >= 0.7
            else IntensityState.ELEVATED if value >= 0.5 else IntensityState.NORMAL
            if value >= 0.2 else IntensityState.LOW)


def narrative_lifecycle(strength: float, velocity: float, persistence: float,
                        reversal: bool = False) -> NarrativeLifecycle:
    if reversal:
        return NarrativeLifecycle.REVERSING
    if strength < 0.1:
        return NarrativeLifecycle.DORMANT
    if velocity > 0.2:
        return NarrativeLifecycle.ACCELERATING
    if persistence >= 0.7 and strength >= 0.75:
        return NarrativeLifecycle.SATURATED
    if persistence >= 0.5:
        return NarrativeLifecycle.ESTABLISHED
    if velocity < -0.15:
        return NarrativeLifecycle.WEAKENING
    return NarrativeLifecycle.EMERGING


def build_psychology_snapshot(
    cutoff: datetime,
    *,
    scope: str,
    scope_id: str,
    observations: list[SentimentObservation],
    narratives: list[Narrative] | None = None,
) -> PsychologySnapshot:
    known = [x for x in observations if x.available_at <= cutoff and
             ((scope == "ENTITY" and x.entity_id == scope_id)
              or (scope == "SECTOR" and x.sector_id == scope_id)
              or (scope == "MARKET" and x.market_id == scope_id))]
    clusters = _unique_clusters(known)
    direction, score, disagreement_value = aggregate_sentiment(known)
    attention = attention_metrics(known, cutoff)
    disagreement = classify_disagreement(disagreement_value, len(clusters))
    negative = sum(DIRECTION_SCORE[x.sentiment_direction] < 0 for x in clusters) / max(1, len(clusters))
    positive = sum(DIRECTION_SCORE[x.sentiment_direction] > 0 for x in clusters) / max(1, len(clusters))
    rumour = sum(x.is_rumour for x in clusters) / max(1, len(clusters))
    uncertainty = min(1.0, disagreement_value + rumour / 2)
    attention_level = min(1.0, attention.attention_percentile / 100)
    fear_value = (negative + uncertainty + attention_level) / 3
    euphoria_value = (positive + max(0, attention.attention_velocity) / 2 + attention_level) / 3
    speculative = min(1.0, (rumour + attention_level + max(0, attention.attention_acceleration)) / 3)
    active_narratives = tuple(x for x in (narratives or []) if x.last_seen <= cutoff and
                              ((scope == "ENTITY" and x.entity_id == scope_id)
                               or (scope == "SECTOR" and x.sector_id == scope_id)
                               or (scope == "MARKET" and x.market_id == scope_id)))
    dominance = max((x.current_strength for x in active_narratives), default=0)
    crowding = (CrowdingState.UNKNOWN if len(active_narratives) == 0 else
                CrowdingState.EXTREME if dominance >= 0.9 else
                CrowdingState.ELEVATED if dominance >= 0.7 else CrowdingState.NORMAL)
    certainty = min(1.0, len(clusters) / 5) * (1 - disagreement_value) * (1 - rumour * 0.75)
    state = ScopeSentimentState(
        scope=scope, scope_id=scope_id, as_of=cutoff, current_sentiment=direction,
        sentiment_trend="UNKNOWN" if len(clusters) < 2 else "STABLE",
        attention=attention, disagreement=disagreement,
        dominant_narratives=tuple(sorted(active_narratives,
                                         key=lambda x: x.current_strength, reverse=True)[:3]),
        material_events=tuple(x.event_id for x in clusters
                              if x.event_id and x.sentiment_strength >= 0.75),
        rumour_burden=rumour, certainty=certainty,
        source_quality="INSUFFICIENT" if len(clusters) < 2 else "TIERED_CLUSTER_WEIGHTED")
    psych = PsychologyObservation(
        attention=attention_level, fear=fear_value, euphoria=euphoria_value,
        uncertainty=uncertainty, disagreement=disagreement_value,
        crowding=dominance, speculative_intensity=speculative,
        narrative_strength=dominance,
        narrative_velocity=max((x.velocity for x in active_narratives), default=0),
        narrative_persistence=max((x.persistence for x in active_narratives), default=0),
        narrative_reversal=float(any(x.status == NarrativeLifecycle.REVERSING
                                     for x in active_narratives)),
        source_diversity=attention.source_diversity,
        information_density=len(clusters) / 5, as_of=cutoff,
        quality=state.source_quality,
        provenance={"cluster_first": True, "score": score, "cutoff_enforced": True})
    return PsychologySnapshot(
        cutoff=cutoff, scope=scope, scope_id=scope_id, observations=tuple(known),
        sentiment=state, psychology=psych, narratives=active_narratives,
        fear_state=classify_intensity(fear_value, len(clusters)),
        euphoria_state=classify_intensity(euphoria_value, len(clusters)),
        uncertainty_state=classify_intensity(uncertainty, len(clusters)),
        crowding_state=crowding,
        speculative_state=classify_intensity(speculative, len(clusters)),
        source_quality=state.source_quality)


class PsychologyEvidenceEngine:
    def evaluate(self, snapshot: PsychologySnapshot, *, horizon: str) -> PsychologyEvidence:
        count = len(_unique_clusters(list(snapshot.observations)))
        insufficient = count < 2 or snapshot.sentiment.certainty < 0.2
        supporting = tuple(ref for item in snapshot.observations
                           if DIRECTION_SCORE[item.sentiment_direction] > 0
                           for ref in item.evidence_refs)
        contradicting = tuple(ref for item in snapshot.observations
                              if DIRECTION_SCORE[item.sentiment_direction] < 0
                              for ref in item.evidence_refs)
        return PsychologyEvidence(
            as_of=snapshot.cutoff, scope=f"{snapshot.scope}:{snapshot.scope_id}", horizon=horizon,
            status="INSUFFICIENT_PSYCHOLOGY_EVIDENCE" if insufficient
            else "INTERNAL_PSYCHOLOGY_EVIDENCE_NOT_PREDICTION",
            sentiment_state=snapshot.sentiment.current_sentiment,
            attention_state=classify_intensity(snapshot.psychology.attention, count),
            fear_state=snapshot.fear_state, euphoria_state=snapshot.euphoria_state,
            uncertainty_state=snapshot.uncertainty_state,
            disagreement_state=snapshot.sentiment.disagreement,
            crowding_state=snapshot.crowding_state, speculative_state=snapshot.speculative_state,
            dominant_narratives=tuple(x.topic for x in snapshot.sentiment.dominant_narratives),
            supporting_evidence=supporting, contradicting_evidence=contradicting,
            certainty=snapshot.sentiment.certainty,
            data_quality=snapshot.source_quality, directional_evidence_score=None,
            explanation_payload={"label": "INTERNAL INTELLIGENCE — NOT PREDICTION",
                                 "sentiment": snapshot.sentiment.current_sentiment,
                                 "not": ["price probability", "expected return", "recommendation"]},
            provenance={"snapshot_hash": snapshot.snapshot_hash, "cluster_first": True})


def sentiment_breadth(states: list[ScopeSentimentState]) -> dict[str, float]:
    eligible = [x for x in states if x.certainty >= 0.2]
    count = max(1, len(eligible))
    buckets = Counter("positive" if DIRECTION_SCORE[x.current_sentiment] > 0 else
                      "negative" if DIRECTION_SCORE[x.current_sentiment] < 0 else
                      "mixed" if x.current_sentiment == SentimentDirection.MIXED else "unknown"
                      for x in eligible)
    return {**{f"{key}_entity_share": buckets[key] / count
               for key in ("positive", "negative", "mixed", "unknown")},
            "high_attention_entity_share": sum(x.attention.attention_percentile >= 80
                                                for x in eligible) / count}


def psychology_qa(records: list[SentimentObservation], snapshots: list[PsychologySnapshot],
                  *, model_disagreements: int = 0) -> dict[str, float | int]:
    unique = sum(len(_unique_clusters(list(x.observations))) for x in snapshots)
    total = sum(len(x.observations) for x in snapshots)
    return {
        "sentiment_processing_count": len(records),
        "unknown_rate": sum(x.sentiment_direction == SentimentDirection.UNKNOWN for x in records)
        / max(1, len(records)),
        "abstention_rate": sum(len(_unique_clusters(list(x.observations))) < 2 for x in snapshots)
        / max(1, len(snapshots)),
        "narrative_count": sum(len(x.narratives) for x in snapshots),
        "duplicate_suppression_rate": (total - unique) / max(1, total),
        "source_diversity": len({x.source_id for x in records}) / max(1, len(records)),
        "model_disagreement_rate": model_disagreements / max(1, len(records)),
    }
