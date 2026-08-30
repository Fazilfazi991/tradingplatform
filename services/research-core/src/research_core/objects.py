from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_core.common import stable_hash


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class ResearchMode(StrEnum):
    ENGINEERING_FIXTURE = "ENGINEERING_FIXTURE"
    EXPLORATORY_REAL = "EXPLORATORY_REAL"
    FORMAL_DISCOVERY = "FORMAL_DISCOVERY"
    SEALED_VALIDATION = "SEALED_VALIDATION"
    HOLDOUT = "HOLDOUT"
    FORWARD = "FORWARD"


class FeatureDefinition(FrozenModel):
    feature_id: str
    name: str
    family: str
    version: str = "1"
    description: str
    lookback: int
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_fields: tuple[str, ...]
    availability_lag: int = 0
    minimum_history: int
    normalization: str = "none"
    null_policy: str = "preserve"
    implementation_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    code_sha: str
    definition_hash: str = ""

    @model_validator(mode="after")
    def hash_definition(self) -> FeatureDefinition:
        if not self.definition_hash:
            payload = self.model_dump(exclude={"definition_hash", "created_at"}, mode="json")
            object.__setattr__(self, "definition_hash", stable_hash(payload))
        return self


class TargetDefinition(FrozenModel):
    target_id: str
    name: str
    version: str = "1"
    description: str
    horizon: int
    target_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    decision_time: str = "AFTER_SESSION_CLOSE"
    entry_assumption: str = "NEXT_SESSION_CLOSE"
    outcome_availability: str = "AFTER_HORIZON_SESSION_CLOSE"
    implementation_path: str
    definition_hash: str = ""

    @model_validator(mode="after")
    def hash_definition(self) -> TargetDefinition:
        if not self.definition_hash:
            object.__setattr__(
                self,
                "definition_hash",
                stable_hash(self.model_dump(exclude={"definition_hash"}, mode="json")),
            )
        return self


class PartitionSpec(FrozenModel):
    name: str
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    calibration_start: datetime | None = None
    calibration_end: datetime | None = None
    purge_sessions: int = 0
    embargo_sessions: int = 0
    expanding: bool = True

    @model_validator(mode="after")
    def chronological(self) -> PartitionSpec:
        if not self.train_start <= self.train_end < self.test_start <= self.test_end:
            raise ValueError("partition dates must be strictly chronological")
        return self


class PredictionExperiment(FrozenModel):
    experiment_id: UUID = Field(default_factory=uuid4)
    name: str
    hypothesis: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dataset_id: str
    feature_set_id: str
    target_id: str
    model_spec: dict[str, Any]
    partition_spec: dict[str, Any]
    primary_metric: str
    secondary_metrics: tuple[str, ...] = ()
    baseline_models: tuple[str, ...] = ()
    multiple_testing_family: str = "single_engineering_hypothesis"
    parameter_budget: dict[str, int] = Field(default_factory=dict)
    code_sha: str
    config_hash: str = ""
    status: str = "REGISTERED"
    decision: str | None = None
    reviewer: str | None = None

    @model_validator(mode="after")
    def hash_config(self) -> PredictionExperiment:
        if not self.config_hash:
            keys = {
                "dataset_id",
                "feature_set_id",
                "target_id",
                "model_spec",
                "partition_spec",
                "code_sha",
            }
            object.__setattr__(
                self,
                "config_hash",
                stable_hash({k: self.model_dump(mode="json")[k] for k in sorted(keys)}),
            )
        return self


class ModelArtifact(FrozenModel):
    model_id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    model_family: str
    version: str
    training_partition: dict[str, Any]
    hyperparameters: dict[str, Any]
    feature_definitions: tuple[str, ...]
    target_definition: str
    artifact_uri: str
    artifact_hash: str
    environment_hash: str
    code_sha: str
    trained_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PredictionRecord(FrozenModel):
    prediction_id: UUID = Field(default_factory=uuid4)
    model_id: UUID
    instrument_id: str
    as_of: datetime
    information_cutoff: datetime
    target_definition: str
    horizon: int
    prediction_type: str
    raw_prediction: float | dict[str, float]
    calibrated_prediction: float | dict[str, float] | None = None
    uncertainty: dict[str, Any]
    evidence_snapshot: dict[str, Any]
    feature_snapshot: dict[str, float | None]
    model_version: str
    dataset_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload_hash: str = ""

    @model_validator(mode="after")
    def validate_cutoff(self) -> PredictionRecord:
        if self.information_cutoff > self.as_of:
            raise ValueError("information_cutoff cannot exceed as_of")
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                stable_hash(self.model_dump(exclude={"payload_hash", "created_at"}, mode="json")),
            )
        return self


class EvidenceEngineOutput(FrozenModel):
    engine_id: str
    engine_version: str
    as_of: datetime
    target: str
    horizon: int
    directional_score: float
    probability_distribution: dict[str, float] | None = None
    confidence_quality: Literal["LOW", "MEDIUM", "HIGH", "UNAVAILABLE"]
    data_quality: Literal["PASS", "WARNING", "BLOCKED"]
    evidence_count: int
    explanation_payload: dict[str, Any]
    contradictions: tuple[str, ...] = ()
    provenance: dict[str, Any]
    status: Literal["RESEARCH", "PLANNED", "BLOCKED"] = "RESEARCH"


class FusionInput(FrozenModel):
    as_of: datetime
    target: str
    horizon: int
    engines: tuple[EvidenceEngineOutput, ...]


class FusionOutput(FrozenModel):
    as_of: datetime
    target: str
    horizon: int
    directional_score: float | None
    agreement: int
    engine_count: int
    contradictions: tuple[str, ...]
    status: Literal["CONTRACT_ONLY"] = "CONTRACT_ONLY"
    note: str = "No production fusion model is implemented."
