from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import model_validator
from research_core.common import stable_hash

from intelligence_core.event_intelligence import (
    ConfirmationState,
    EventDirection,
    EventIntelligence,
    Materiality,
    NoveltyState,
)
from intelligence_core.models import FrozenModel


class EvidenceContribution(FrozenModel):
    event_intelligence_id: str
    orientation: str
    weight: float
    reason: str
    duplicate_penalty: float
    contradiction_penalty: float
    time_decay_metadata: dict[str, Any]


class NewsEvidenceOutput(FrozenModel):
    engine_id: str = "NEWS_EVENT_EVIDENCE"
    engine_version: str = "1"
    as_of: datetime
    entity_id: str
    horizon: str
    status: str
    event_count: int
    material_event_count: int
    positive_evidence: float
    negative_evidence: float
    mixed_evidence: float
    novelty_state: str
    attention_state: str
    contradictions: tuple[str, ...]
    source_quality: str
    certainty_quality: str
    directional_evidence_score: float | None
    contributions: tuple[EvidenceContribution, ...]
    explanation_payload: dict[str, Any]
    provenance: dict[str, Any]
    payload_hash: str = ""

    @model_validator(mode="after")
    def hash_output(self) -> NewsEvidenceOutput:
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                stable_hash(self.model_dump(exclude={"payload_hash"}, mode="json")),
            )
        return self


class NewsEventEvidenceEngine:
    version = "1"

    def evaluate(
        self,
        *,
        entity_id: str,
        cutoff: datetime,
        horizon: str,
        intelligence: list[EventIntelligence],
    ) -> NewsEvidenceOutput:
        eligible = [
            record
            for record in intelligence
            if record.available_at <= cutoff
            and (
                record.primary_entity_id in {None, entity_id}
                or any(item.entity_id == entity_id for item in record.affected_entities)
            )
            and horizon in record.potential_horizon
        ]
        seen_clusters = set()
        contributions = []
        positive = negative = mixed = 0.0
        for record in sorted(
            eligible, key=lambda item: (item.available_at, str(item.event_intelligence_id))
        ):
            duplicate = (
                record.cluster_id in seen_clusters or record.novelty == NoveltyState.DUPLICATE
            )
            seen_clusters.add(record.cluster_id)
            duplicate_penalty = 0.0 if duplicate else 1.0
            contradiction_penalty = 0.5 if record.contradictions else 1.0
            confirmation = {
                ConfirmationState.OFFICIAL_CONFIRMED: 1.0,
                ConfirmationState.MULTI_SOURCE_CONFIRMED: 0.9,
                ConfirmationState.SINGLE_REPUTABLE_SOURCE: 0.65,
                ConfirmationState.UNVERIFIED: 0.25,
                ConfirmationState.RUMOUR: 0.1,
            }.get(record.confirmation_state, 0.2)
            materiality = {
                Materiality.IMMATERIAL: 0.1,
                Materiality.LOW: 0.25,
                Materiality.MEDIUM: 0.5,
                Materiality.HIGH: 0.75,
                Materiality.MATERIAL: 0.9,
                Materiality.SYSTEMIC: 1.0,
                Materiality.UNKNOWN: 0.2,
            }[record.materiality]
            weight = (
                record.certainty
                * confirmation
                * materiality
                * duplicate_penalty
                * contradiction_penalty
            )
            orientation = "NEUTRAL"
            if record.direction in {EventDirection.POSITIVE, EventDirection.STRONGLY_POSITIVE}:
                positive += weight
                orientation = "POSITIVE"
            elif record.direction in {EventDirection.NEGATIVE, EventDirection.STRONGLY_NEGATIVE}:
                negative += weight
                orientation = "NEGATIVE"
            elif record.direction == EventDirection.MIXED:
                mixed += weight
                orientation = "MIXED"
            contributions.append(
                EvidenceContribution(
                    event_intelligence_id=str(record.event_intelligence_id),
                    orientation=orientation,
                    weight=weight,
                    reason=f"{record.materiality}/{record.confirmation_state}/{record.novelty}",
                    duplicate_penalty=duplicate_penalty,
                    contradiction_penalty=contradiction_penalty,
                    time_decay_metadata={
                        "event_type": record.event_type,
                        "horizon": horizon,
                        "final_decay_constant": "NOT_SELECTED",
                    },
                )
            )
        directional = (
            None if not eligible else (positive - negative) / max(positive + negative + mixed, 1e-9)
        )
        certainty = (
            "INSUFFICIENT"
            if not eligible
            else "LOW"
            if any(item.contradictions for item in eligible)
            else "MEDIUM"
        )
        return NewsEvidenceOutput(
            as_of=cutoff,
            entity_id=entity_id,
            horizon=horizon,
            status="INSUFFICIENT_INTELLIGENCE" if not eligible else "EVIDENCE_ONLY_NOT_PREDICTION",
            event_count=len(eligible),
            material_event_count=sum(
                item.materiality in {Materiality.MATERIAL, Materiality.SYSTEMIC}
                for item in eligible
            ),
            positive_evidence=positive,
            negative_evidence=negative,
            mixed_evidence=mixed,
            novelty_state="NO_EVENTS" if not eligible else "MIXED_NOVELTY",
            attention_state="NOT_PREDICTIVE",
            contradictions=tuple(
                str(item.contradiction_id) for record in eligible for item in record.contradictions
            ),
            source_quality="TIERED_NOT_COUNT_WEIGHTED",
            certainty_quality=certainty,
            directional_evidence_score=directional,
            contributions=tuple(contributions),
            explanation_payload={
                "label": "evidence orientation only",
                "not": ["price-rise probability", "expected return", "buy/sell score"],
            },
            provenance={"engine_version": self.version, "cutoff_enforced": True},
        )


def qa_metrics(records: list[EventIntelligence], total_input_events: int) -> dict[str, float]:
    count = len(records)
    return {
        "classification_coverage": count / max(1, total_input_events),
        "unknown_rate": sum(record.direction == EventDirection.UNKNOWN for record in records)
        / max(1, count),
        "entity_match_rate": sum(record.primary_entity_id is not None for record in records)
        / max(1, count),
        "materiality_unknown_rate": sum(
            record.materiality == Materiality.UNKNOWN for record in records
        )
        / max(1, count),
        "contradiction_rate": sum(bool(record.contradictions) for record in records)
        / max(1, count),
        "duplicate_suppression_rate": sum(
            record.novelty == NoveltyState.DUPLICATE for record in records
        )
        / max(1, count),
        "llm_validation_failure_rate": 0.0,
    }
