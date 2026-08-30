from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import Field, model_validator
from research_core.common import stable_hash

from intelligence_core.models import FrozenModel


class EvidenceOrientation(StrEnum):
    STRONGLY_SUPPORTIVE = "STRONGLY_SUPPORTIVE"
    SUPPORTIVE = "SUPPORTIVE"
    SLIGHTLY_SUPPORTIVE = "SLIGHTLY_SUPPORTIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    SLIGHTLY_ADVERSE = "SLIGHTLY_ADVERSE"
    ADVERSE = "ADVERSE"
    STRONGLY_ADVERSE = "STRONGLY_ADVERSE"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class QualityTier(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"
    UNKNOWN = "UNKNOWN"


class EngineStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INSUFFICIENT = "INSUFFICIENT"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class DependencyType(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    PARTIALLY_OVERLAPPING = "PARTIALLY_OVERLAPPING"
    HIGHLY_OVERLAPPING = "HIGHLY_OVERLAPPING"
    DERIVED_FROM = "DERIVED_FROM"
    UNKNOWN = "UNKNOWN"


class AgreementState(StrEnum):
    STRONG_AGREEMENT = "STRONG_AGREEMENT"
    MODERATE_AGREEMENT = "MODERATE_AGREEMENT"
    WEAK_AGREEMENT = "WEAK_AGREEMENT"
    MIXED = "MIXED"
    STRONG_CONFLICT = "STRONG_CONFLICT"
    INSUFFICIENT = "INSUFFICIENT"


class UncertaintyState(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNKNOWN = "UNKNOWN"


class FusionState(StrEnum):
    STRONGLY_SUPPORTIVE = "STRONGLY_SUPPORTIVE"
    SUPPORTIVE = "SUPPORTIVE"
    SLIGHTLY_SUPPORTIVE = "SLIGHTLY_SUPPORTIVE"
    BALANCED = "BALANCED"
    CONFLICTED = "CONFLICTED"
    SLIGHTLY_ADVERSE = "SLIGHTLY_ADVERSE"
    ADVERSE = "ADVERSE"
    STRONGLY_ADVERSE = "STRONGLY_ADVERSE"
    INSUFFICIENT = "INSUFFICIENT"
    ABSTAIN = "ABSTAIN"


class EvidenceQuality(FrozenModel):
    source_quality: float = Field(ge=0, le=1)
    data_quality: float = Field(ge=0, le=1)
    coverage: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    certainty: float = Field(ge=0, le=1)
    causal_integrity: float = Field(ge=0, le=1)
    sample_adequacy: float = Field(ge=0, le=1)
    validation_status: str
    tier: QualityTier


class SpecialistEvidenceOutput(FrozenModel):
    engine_id: str
    engine_family: str
    engine_version: str
    scope: str
    entity_id: str | None = None
    sector_id: str | None = None
    market_id: str | None = None
    as_of: datetime
    horizon: str
    status: EngineStatus
    evidence_orientation: EvidenceOrientation
    certainty: float = Field(ge=0, le=1)
    data_quality: str
    freshness: float = Field(ge=0, le=1)
    coverage: float = Field(ge=0, le=1)
    supporting_evidence: tuple[str, ...] = ()
    adverse_evidence: tuple[str, ...] = ()
    neutral_evidence: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any]
    snapshot_hash: str
    payload_hash: str = ""
    source_quality: float = Field(default=0.5, ge=0, le=1)
    causal_integrity: float = Field(default=1, ge=0, le=1)
    sample_adequacy: float = Field(default=0.5, ge=0, le=1)
    validation_status: str = "ENGINEERING_ONLY"
    feature_families: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()
    cluster_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def causal_hash(self) -> SpecialistEvidenceOutput:
        if (self.status in {EngineStatus.INSUFFICIENT, EngineStatus.BLOCKED, EngineStatus.FAILED}
                and self.evidence_orientation not in {
                    EvidenceOrientation.UNKNOWN, EvidenceOrientation.INSUFFICIENT_EVIDENCE}):
            raise ValueError("unavailable engine cannot carry directional orientation")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(
                self.model_dump(exclude={"payload_hash"}, mode="json")))
        return self


class EngineDependency(FrozenModel):
    engine_a: str
    engine_b: str
    dependency_type: DependencyType
    shared_source_ids: tuple[str, ...] = ()
    shared_event_ids: tuple[str, ...] = ()
    shared_cluster_ids: tuple[str, ...] = ()
    shared_feature_families: tuple[str, ...] = ()
    reason: str

    @property
    def independence_factor(self) -> float:
        return {
            DependencyType.INDEPENDENT: 1.0,
            DependencyType.PARTIALLY_OVERLAPPING: 0.65,
            DependencyType.HIGHLY_OVERLAPPING: 0.35,
            DependencyType.DERIVED_FROM: 0.2,
            DependencyType.UNKNOWN: 0.5,
        }[self.dependency_type]


class EngineDependencyGraph(FrozenModel):
    dependencies: tuple[EngineDependency, ...]

    def factor_for(self, engine_id: str) -> float:
        factors = [x.independence_factor for x in self.dependencies
                   if engine_id in {x.engine_a, x.engine_b}]
        return min(factors, default=1.0)


class EvidenceContribution(FrozenModel):
    engine: str
    evidence_id: str
    orientation: EvidenceOrientation
    quality: QualityTier
    relevance: str
    horizon_relevance: str
    freshness: float
    independence_factor: float
    contribution_state: str
    reason: str
    provenance: dict[str, Any]


class FusionContradiction(FrozenModel):
    engine_a: str
    engine_b: str
    evidence_a: tuple[str, ...]
    evidence_b: tuple[str, ...]
    severity: str
    type: str
    reason: str
    shared_provenance: tuple[str, ...] = ()
    resolution_status: str = "UNRESOLVED"


class EvidenceAgreement(FrozenModel):
    state: AgreementState
    supportive_engines: tuple[str, ...]
    adverse_engines: tuple[str, ...]
    mixed_engines: tuple[str, ...]
    unknown_engines: tuple[str, ...]
    high_quality_supportive: tuple[str, ...]
    high_quality_adverse: tuple[str, ...]


class FusionUncertainty(FrozenModel):
    engine_disagreement: str
    missing_evidence: str
    low_quality: str
    staleness: str
    dependency: str
    sample_adequacy: str
    source_conflict: str
    model_disagreement: str
    regime_uncertainty: str
    state: UncertaintyState


class FusionPolicy(FrozenModel):
    minimum_eligible_engines: int = 2
    minimum_medium_quality: int = 1
    maximum_missing_engines: int = 4
    strong_state_minimum_independent_engines: int = 4
    version: str = "fusion-v0"


class FusionSnapshot(FrozenModel):
    scope: str
    cutoff: datetime
    horizon: str
    engine_snapshots: tuple[SpecialistEvidenceOutput, ...]
    dependencies: EngineDependencyGraph
    agreement: EvidenceAgreement
    contradictions: tuple[FusionContradiction, ...]
    uncertainty: FusionUncertainty
    fusion_state: FusionState
    abstention: tuple[str, ...]
    contributions: tuple[EvidenceContribution, ...]
    explanation: dict[str, Any]
    provenance: dict[str, Any]
    fusion_version: str
    payload_hash: str = ""

    @model_validator(mode="after")
    def cutoff_hash(self) -> FusionSnapshot:
        if any(x.as_of > self.cutoff for x in self.engine_snapshots):
            raise ValueError("fusion contains a specialist snapshot generated after cutoff")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(
                self.model_dump(exclude={"payload_hash"}, mode="json")))
        return self


class LearnedFusionModel(Protocol):
    status: str

    def predict(self, outputs: tuple[SpecialistEvidenceOutput, ...]) -> Any: ...


LEARNED_FUSION_STATUS = "NOT_VALIDATED_DISABLED"
ENGINE_FRESHNESS_METADATA = {
    "TECHNICAL": "LAST_COMPLETED_SESSION",
    "HISTORICAL": "EXPERIMENT_VERSION_BOUND",
    "NEWS_EVENT": "MINUTES_TO_HOURS_BY_EVENT",
    "MACRO_GLOBAL": "RELEASE_DEPENDENT",
    "FUNDAMENTAL": "FILING_DEPENDENT_WEEKS_TO_MONTHS",
    "PSYCHOLOGY": "MINUTES_TO_DAYS",
    "FLOW_DERIVATIVES": "INTRADAY_OR_EOD_BY_SOURCE",
}
ORIENTATION_SIGN = {
    EvidenceOrientation.STRONGLY_SUPPORTIVE: 1,
    EvidenceOrientation.SUPPORTIVE: 1,
    EvidenceOrientation.SLIGHTLY_SUPPORTIVE: 1,
    EvidenceOrientation.NEUTRAL: 0,
    EvidenceOrientation.MIXED: 0,
    EvidenceOrientation.SLIGHTLY_ADVERSE: -1,
    EvidenceOrientation.ADVERSE: -1,
    EvidenceOrientation.STRONGLY_ADVERSE: -1,
    EvidenceOrientation.UNKNOWN: 0,
    EvidenceOrientation.INSUFFICIENT_EVIDENCE: 0,
}
QUALITY_RANK = {QualityTier.UNKNOWN: 0, QualityTier.VERY_LOW: 1, QualityTier.LOW: 2,
                QualityTier.MEDIUM: 3, QualityTier.HIGH: 4, QualityTier.VERY_HIGH: 5}


def evidence_quality(item: SpecialistEvidenceOutput) -> EvidenceQuality:
    values = (item.source_quality, 1.0 if item.data_quality == "PASS" else 0.5,
              item.coverage, item.freshness, item.certainty, item.causal_integrity,
              item.sample_adequacy)
    score = sum(values) / len(values)
    tier = (QualityTier.VERY_HIGH if score >= 0.9 else QualityTier.HIGH if score >= 0.75 else
            QualityTier.MEDIUM if score >= 0.55 else QualityTier.LOW if score >= 0.35 else
            QualityTier.VERY_LOW)
    if item.status in {EngineStatus.STALE, EngineStatus.INSUFFICIENT, EngineStatus.FAILED}:
        tier = QualityTier.VERY_LOW
    return EvidenceQuality(source_quality=item.source_quality,
                           data_quality=values[1], coverage=item.coverage,
                           freshness=item.freshness, certainty=item.certainty,
                           causal_integrity=item.causal_integrity,
                           sample_adequacy=item.sample_adequacy,
                           validation_status=item.validation_status, tier=tier)


def dependency_graph(outputs: tuple[SpecialistEvidenceOutput, ...]) -> EngineDependencyGraph:
    dependencies = []
    for index, left in enumerate(outputs):
        for right in outputs[index + 1:]:
            shared_sources = tuple(sorted(set(left.source_ids) & set(right.source_ids)))
            shared_events = tuple(sorted(set(left.event_ids) & set(right.event_ids)))
            shared_clusters = tuple(sorted(set(left.cluster_ids) & set(right.cluster_ids)))
            shared_features = tuple(sorted(set(left.feature_families) & set(right.feature_families)))
            overlap = len(shared_sources) + len(shared_events) + len(shared_clusters) + len(shared_features)
            kind = (DependencyType.HIGHLY_OVERLAPPING if overlap >= 3 else
                    DependencyType.PARTIALLY_OVERLAPPING if overlap else DependencyType.INDEPENDENT)
            dependencies.append(EngineDependency(
                engine_a=left.engine_id, engine_b=right.engine_id, dependency_type=kind,
                shared_source_ids=shared_sources, shared_event_ids=shared_events,
                shared_cluster_ids=shared_clusters, shared_feature_families=shared_features,
                reason="shared provenance discounted" if overlap else "no declared shared provenance"))
    return EngineDependencyGraph(dependencies=tuple(dependencies))


def _eligible(item: SpecialistEvidenceOutput) -> bool:
    return (item.status in {EngineStatus.AVAILABLE, EngineStatus.PARTIAL}
            and item.freshness > 0 and item.evidence_orientation not in {
                EvidenceOrientation.UNKNOWN, EvidenceOrientation.INSUFFICIENT_EVIDENCE})


def agreement(outputs: tuple[SpecialistEvidenceOutput, ...]) -> EvidenceAgreement:
    eligible = [x for x in outputs if _eligible(x)]
    supportive = tuple(x.engine_id for x in eligible if ORIENTATION_SIGN[x.evidence_orientation] > 0)
    adverse = tuple(x.engine_id for x in eligible if ORIENTATION_SIGN[x.evidence_orientation] < 0)
    mixed = tuple(x.engine_id for x in eligible if x.evidence_orientation in {
        EvidenceOrientation.MIXED, EvidenceOrientation.NEUTRAL})
    unknown = tuple(x.engine_id for x in outputs if x not in eligible)
    high_support = tuple(x.engine_id for x in eligible if x.engine_id in supportive
                         and QUALITY_RANK[evidence_quality(x).tier] >= 4)
    high_adverse = tuple(x.engine_id for x in eligible if x.engine_id in adverse
                         and QUALITY_RANK[evidence_quality(x).tier] >= 4)
    if len(eligible) < 2:
        state = AgreementState.INSUFFICIENT
    elif high_support and high_adverse:
        state = AgreementState.STRONG_CONFLICT
    elif supportive and adverse:
        state = AgreementState.MIXED
    else:
        dominant = max(len(supportive), len(adverse))
        state = (AgreementState.STRONG_AGREEMENT if dominant >= 5 else
                 AgreementState.MODERATE_AGREEMENT if dominant >= 3 else AgreementState.WEAK_AGREEMENT)
    return EvidenceAgreement(state=state, supportive_engines=supportive, adverse_engines=adverse,
                             mixed_engines=mixed, unknown_engines=unknown,
                             high_quality_supportive=high_support, high_quality_adverse=high_adverse)


def contradictions(outputs: tuple[SpecialistEvidenceOutput, ...],
                   graph: EngineDependencyGraph) -> tuple[FusionContradiction, ...]:
    result = []
    eligible = [x for x in outputs if _eligible(x)]
    for index, left in enumerate(eligible):
        for right in eligible[index + 1:]:
            if ORIENTATION_SIGN[left.evidence_orientation] * ORIENTATION_SIGN[right.evidence_orientation] < 0:
                qualities = (evidence_quality(left).tier, evidence_quality(right).tier)
                severity = "HIGH" if all(QUALITY_RANK[x] >= 4 for x in qualities) else "MEDIUM"
                dep = next((x for x in graph.dependencies if {x.engine_a, x.engine_b}
                            == {left.engine_id, right.engine_id}), None)
                result.append(FusionContradiction(
                    engine_a=left.engine_id, engine_b=right.engine_id,
                    evidence_a=left.supporting_evidence or left.adverse_evidence,
                    evidence_b=right.supporting_evidence or right.adverse_evidence,
                    severity=severity, type="DIRECTIONAL",
                    reason=f"{left.evidence_orientation} opposes {right.evidence_orientation}",
                    shared_provenance=dep.shared_cluster_ids if dep else ()))
    return tuple(result)


def fuse_specialist_outputs(outputs: tuple[SpecialistEvidenceOutput, ...],
                            policy: FusionPolicy | None = None,
                            *, cutoff: datetime | None = None) -> FusionSnapshot:
    policy = policy or FusionPolicy()
    if not outputs:
        raise ValueError("fusion requires specialist outputs")
    cutoff = cutoff or max(x.as_of for x in outputs)
    scope, horizon = outputs[0].scope, outputs[0].horizon
    if any(x.scope != scope or x.horizon != horizon for x in outputs):
        raise ValueError("fusion inputs must share scope and horizon")
    graph = dependency_graph(outputs)
    agree = agreement(outputs)
    conflicts = contradictions(outputs, graph)
    eligible = [x for x in outputs if _eligible(x)]
    medium = [x for x in eligible if QUALITY_RANK[evidence_quality(x).tier] >= 3]
    missing = 7 - len(eligible)
    high_dependency = any(x.dependency_type in {
        DependencyType.HIGHLY_OVERLAPPING, DependencyType.DERIVED_FROM} for x in graph.dependencies)
    stale = any(x.status == EngineStatus.STALE or x.freshness == 0 for x in outputs)
    model_disagreement = any("MODEL_DISAGREEMENT" in x.warnings for x in outputs)
    reasons = []
    if len(eligible) < policy.minimum_eligible_engines or not medium:
        reasons.append("INSUFFICIENT_HIGH_QUALITY_EVIDENCE")
    if missing > policy.maximum_missing_engines:
        reasons.append("EXCESSIVE_MISSING_ENGINES")
    if agree.state == AgreementState.STRONG_CONFLICT:
        reasons.append("STRONG_ENGINE_CONFLICT")
    if stale and len(eligible) < policy.minimum_eligible_engines + 1:
        reasons.append("STALE_EVIDENCE")
    if high_dependency and len(eligible) < 3:
        reasons.append("DEPENDENCY_TOO_HIGH")
    if model_disagreement:
        reasons.append("MODEL_DISAGREEMENT")
    uncertainty_state = (UncertaintyState.VERY_HIGH if reasons or len(conflicts) >= 2 else
                         UncertaintyState.HIGH if conflicts or missing >= 3 else
                         UncertaintyState.MEDIUM if missing else UncertaintyState.LOW)
    uncertainty = FusionUncertainty(
        engine_disagreement="HIGH" if conflicts else "LOW",
        missing_evidence="HIGH" if missing >= 3 else "LOW",
        low_quality="HIGH" if len(medium) < max(1, len(eligible) // 2) else "LOW",
        staleness="PRESENT" if stale else "NONE", dependency="HIGH" if high_dependency else "LOW",
        sample_adequacy="LOW" if len(eligible) < 3 else "MEDIUM",
        source_conflict="PRESENT" if any(x.contradictions for x in outputs) else "NONE",
        model_disagreement="PRESENT" if model_disagreement else "NONE",
        regime_uncertainty="UNKNOWN", state=uncertainty_state)
    supportive_quality = sum(QUALITY_RANK[evidence_quality(x).tier] * graph.factor_for(x.engine_id)
                             for x in eligible if ORIENTATION_SIGN[x.evidence_orientation] > 0)
    adverse_quality = sum(QUALITY_RANK[evidence_quality(x).tier] * graph.factor_for(x.engine_id)
                          for x in eligible if ORIENTATION_SIGN[x.evidence_orientation] < 0)
    if reasons:
        state = FusionState.ABSTAIN
    elif supportive_quality and adverse_quality:
        state = FusionState.CONFLICTED
    elif supportive_quality > 0:
        state = FusionState.SUPPORTIVE if supportive_quality >= 6 else FusionState.SLIGHTLY_SUPPORTIVE
    elif adverse_quality > 0:
        state = FusionState.ADVERSE if adverse_quality >= 6 else FusionState.SLIGHTLY_ADVERSE
    else:
        state = FusionState.BALANCED if eligible else FusionState.INSUFFICIENT
    contributions = tuple(EvidenceContribution(
        engine=x.engine_id, evidence_id=x.snapshot_hash, orientation=x.evidence_orientation,
        quality=evidence_quality(x).tier, relevance="SCOPE_MATCHED",
        horizon_relevance="DECLARED_BY_SPECIALIST", freshness=x.freshness,
        independence_factor=graph.factor_for(x.engine_id),
        contribution_state="ELIGIBLE" if _eligible(x) else "INSUFFICIENT",
        reason="quality-tier and dependency-aware categorical contribution",
        provenance={"snapshot_hash": x.snapshot_hash, "payload_hash": x.payload_hash}) for x in outputs)
    explanation = {
        "why": f"{agree.state}; quality precedes engine count",
        "supports": [f"{x.engine_id}: {evidence_quality(x).tier}" for x in eligible
                     if ORIENTATION_SIGN[x.evidence_orientation] > 0],
        "opposes": [f"{x.engine_id}: {evidence_quality(x).tier}" for x in eligible
                    if ORIENTATION_SIGN[x.evidence_orientation] < 0],
        "disagreements": [x.reason for x in conflicts],
        "missing": [x.engine_id for x in outputs if not _eligible(x)],
        "what_would_change": ["resolve high-quality contradictions", "restore missing fresh engines",
                              "add independent evidence rather than repeated provenance"],
        "abstained_because": reasons,
        "not": ["return probability", "expected return", "buy/sell recommendation"],
    }
    return FusionSnapshot(scope=scope, cutoff=cutoff, horizon=horizon, engine_snapshots=outputs,
                          dependencies=graph, agreement=agree, contradictions=conflicts,
                          uncertainty=uncertainty, fusion_state=state, abstention=tuple(reasons),
                          contributions=contributions, explanation=explanation,
                          provenance={"causal_cutoff_enforced": True, "learned_fusion": "DISABLED"},
                          fusion_version=policy.version)


def fuse_evidence(scope: str, cutoff: datetime, horizon: str,
                  outputs: tuple[SpecialistEvidenceOutput, ...]) -> FusionSnapshot:
    selected = tuple(x for x in outputs if x.scope == scope and x.horizon == horizon and x.as_of <= cutoff)
    return fuse_specialist_outputs(selected, cutoff=cutoff)


def engine_removal_analysis(snapshot: FusionSnapshot) -> dict[str, FusionState]:
    result = {"ORIGINAL": snapshot.fusion_state}
    for item in snapshot.engine_snapshots:
        remaining = tuple(x for x in snapshot.engine_snapshots if x.engine_id != item.engine_id)
        result[f"WITHOUT_{item.engine_id}"] = fuse_specialist_outputs(
            remaining, cutoff=snapshot.cutoff).fusion_state if remaining else FusionState.INSUFFICIENT
    return result


def dominance_warning(snapshot: FusionSnapshot) -> str | None:
    removal = engine_removal_analysis(snapshot)
    changes = [key.removeprefix("WITHOUT_") for key, state in removal.items()
               if key != "ORIGINAL" and state != snapshot.fusion_state]
    return f"ENGINE_DOMINANCE:{changes[0]}" if len(changes) == 1 else None


def sensitivity_analysis(snapshot: FusionSnapshot) -> dict[str, FusionState]:
    first = snapshot.engine_snapshots[0]
    downgraded = first.model_copy(update={"source_quality": 0.1, "data_quality": "LOW"})
    stale = first.model_copy(update={"freshness": 0, "status": EngineStatus.STALE})
    return {
        "ORIGINAL": snapshot.fusion_state,
        "FIRST_ENGINE_QUALITY_DOWNGRADE": fuse_specialist_outputs(
            (downgraded, *snapshot.engine_snapshots[1:]), cutoff=snapshot.cutoff).fusion_state,
        "FIRST_ENGINE_STALE": fuse_specialist_outputs(
            (stale, *snapshot.engine_snapshots[1:]), cutoff=snapshot.cutoff).fusion_state,
        "FIRST_ENGINE_MISSING": fuse_specialist_outputs(
            snapshot.engine_snapshots[1:], cutoff=snapshot.cutoff).fusion_state,
    }


def fusion_qa(snapshots: list[FusionSnapshot]) -> dict[str, Any]:
    count = len(snapshots)
    return {
        "fusion_count": count,
        "abstention_rate": sum(bool(x.abstention) for x in snapshots) / max(1, count),
        "insufficient_rate": sum(x.fusion_state == FusionState.INSUFFICIENT for x in snapshots)
        / max(1, count),
        "conflict_rate": sum(bool(x.contradictions) for x in snapshots) / max(1, count),
        "agreement_distribution": {state: sum(x.agreement.state == state for x in snapshots)
                                   for state in AgreementState},
        "uncertainty_distribution": {state: sum(x.uncertainty.state == state for x in snapshots)
                                     for state in UncertaintyState},
        "engine_availability": {engine: sum(any(y.engine_id == engine and _eligible(y)
                                                for y in x.engine_snapshots) for x in snapshots)
                                for engine in {y.engine_id for x in snapshots for y in x.engine_snapshots}},
        "engine_dominance": sum(dominance_warning(x) is not None for x in snapshots),
        "dependency_penalties": sum(x.independence_factor < 1 for snapshot in snapshots
                                    for x in snapshot.contributions),
        "contribution_count": sum(len(x.contributions) for x in snapshots),
    }
