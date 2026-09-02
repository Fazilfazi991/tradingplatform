from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from research_core.common import stable_hash


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class SourceCategory(StrEnum):
    MARKET = "MARKET"
    CORPORATE_FILING = "CORPORATE_FILING"
    CORPORATE_EVENT = "CORPORATE_EVENT"
    NEWS = "NEWS"
    FUNDAMENTAL = "FUNDAMENTAL"
    MACRO = "MACRO"
    SENTIMENT = "SENTIMENT"
    PSYCHOLOGY = "PSYCHOLOGY"
    FLOW = "FLOW"
    DERIVATIVES = "DERIVATIVES"
    SECTOR = "SECTOR"
    GLOBAL_MARKET = "GLOBAL_MARKET"
    ALTERNATIVE = "ALTERNATIVE"


class AccessMethod(StrEnum):
    OFFICIAL_API = "OFFICIAL_API"
    OFFICIAL_FEED = "OFFICIAL_FEED"
    OFFICIAL_FILE = "OFFICIAL_DOWNLOADABLE_FILE"
    OFFICIAL_RSS = "OFFICIAL_RSS"
    LICENSED_API = "LICENSED_COMMERCIAL_API"
    PUBLIC_WEB = "PERMITTED_PUBLIC_WEB_ACCESS"
    CRAWLING = "PERMITTED_CRAWLING"
    BROWSER = "BROWSER_AUTOMATION_LAST_RESORT"
    FIXTURE = "FIXTURE"


class SourceStatus(StrEnum):
    ACTIVE_FIXTURE = "ACTIVE_FIXTURE"
    ACTIVE_INTERNAL = "ACTIVE_INTERNAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED_LICENSE = "BLOCKED_LICENSE"
    PLANNED = "PLANNED"


class ReliabilityTier(StrEnum):
    TIER_1_PRIMARY = "TIER_1_PRIMARY"
    TIER_2_HIGH_QUALITY_SECONDARY = "TIER_2_HIGH_QUALITY_SECONDARY"
    TIER_3_SECONDARY = "TIER_3_SECONDARY"
    TIER_4_UNVERIFIED = "TIER_4_UNVERIFIED"
    TIER_5_REJECTED = "TIER_5_REJECTED"


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    FAILING = "FAILING"
    DISABLED = "DISABLED"
    UNKNOWN = "UNKNOWN"


class HealthAlert(StrEnum):
    SOURCE_STALE = "SOURCE_STALE"
    SCHEMA_CHANGED = "SCHEMA_CHANGED"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    PARSER_FAILED = "PARSER_FAILED"
    DATA_VOLUME_ANOMALY = "DATA_VOLUME_ANOMALY"
    ENTITY_RESOLUTION_SPIKE = "ENTITY_RESOLUTION_SPIKE"


class CollectionMode(StrEnum):
    BACKFILL = "BACKFILL"
    LIVE = "LIVE"
    REPLAY = "REPLAY"
    FIXTURE = "FIXTURE"


class IntelligenceRuntimeMode(StrEnum):
    FIXTURE = "FIXTURE"
    INTERNAL_LIVE = "INTERNAL_LIVE"
    PRODUCTION_INTERNAL = "PRODUCTION_INTERNAL"
    CUSTOMER_VISIBLE = "CUSTOMER_VISIBLE"


class IntelligenceRuntimePolicy:
    maximum_mode = IntelligenceRuntimeMode.INTERNAL_LIVE

    @classmethod
    def authorize(cls, mode: IntelligenceRuntimeMode) -> None:
        if mode not in {IntelligenceRuntimeMode.FIXTURE, IntelligenceRuntimeMode.INTERNAL_LIVE}:
            raise PermissionError(f"intelligence runtime mode blocked: {mode}")


class IntelligenceSource(FrozenModel):
    source_id: str
    name: str
    source_category: SourceCategory
    provider: str
    base_url: HttpUrl
    access_method: AccessMethod
    official_status: bool
    country: str = "IN"
    markets: tuple[str, ...] = ()
    entities_supported: tuple[str, ...] = ()
    content_types: tuple[str, ...] = ()
    update_frequency: str
    expected_latency_seconds: int
    terms_url: HttpUrl | None = None
    robots_url: HttpUrl | None = None
    license_status: SourceStatus
    commercial_status: str = "UNKNOWN"
    internal_research_status: str = "REVIEW_REQUIRED"
    redistribution_status: str = "PROHIBITED_UNLESS_APPROVED"
    retention_status: str = "METADATA_ONLY"
    authentication_type: str = "NONE"
    secret_name: str | None = None
    rate_limit_policy: str
    reliability_tier: ReliabilityTier
    predictive_status: str = "UNKNOWN"
    collector_version: str = "1"
    parser_version: str = "1"
    active: bool = False
    health_status: HealthStatus = HealthStatus.UNKNOWN
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CollectionPolicy(FrozenModel):
    source_id: str
    cadence_seconds: int
    maximum_requests: int = 1
    retries: int = 2
    backoff_seconds: float = 2
    timeout_seconds: float = 10
    maximum_bytes: int = 2_000_000
    cache_policy: str = "ETAG"
    dedupe_policy: str = "CONTENT_HASH"
    retention_policy: str = "RIGHTS_AWARE"
    priority: int = 50
    market_hours_behavior: str = "NORMAL"
    after_hours_behavior: str = "NORMAL"
    failure_threshold: int = 3

    @model_validator(mode="after")
    def conservative(self) -> CollectionPolicy:
        if self.cadence_seconds < 900 or self.maximum_requests < 1 or self.maximum_requests > 20:
            raise ValueError("collection policy exceeds conservative polling limits")
        return self


class EventType(StrEnum):
    EARNINGS = "EARNINGS"
    GUIDANCE = "GUIDANCE"
    ORDER_WIN = "ORDER_WIN"
    ORDER_LOSS = "ORDER_LOSS"
    MERGER = "MERGER"
    ACQUISITION = "ACQUISITION"
    DIVESTMENT = "DIVESTMENT"
    BOARD_MEETING = "BOARD_MEETING"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    LEGAL_EVENT = "LEGAL_EVENT"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    BONUS = "BONUS"
    BUYBACK = "BUYBACK"
    CAPITAL_RAISE = "CAPITAL_RAISE"
    DEBT_CHANGE = "DEBT_CHANGE"
    RATING_CHANGE = "RATING_CHANGE"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    CAPACITY_EXPANSION = "CAPACITY_EXPANSION"
    CONTRACT = "CONTRACT"
    PARTNERSHIP = "PARTNERSHIP"
    GOVERNMENT_POLICY = "GOVERNMENT_POLICY"
    SECTOR_POLICY = "SECTOR_POLICY"
    MACRO_RELEASE = "MACRO_RELEASE"
    CENTRAL_BANK = "CENTRAL_BANK"
    GEOPOLITICAL = "GEOPOLITICAL"
    COMMODITY_SHOCK = "COMMODITY_SHOCK"
    ANALYST_ACTION = "ANALYST_ACTION"
    OTHER = "OTHER"


class InformationEvent(FrozenModel):
    event_id: UUID = Field(default_factory=uuid4)
    entity_id: str | None = None
    entity_type: str
    source_id: str
    source_event_id: str | None = None
    event_type: EventType
    event_subtype: str | None = None
    title: str
    summary: str
    canonical_url: HttpUrl | None = None
    raw_artifact_uri: str
    raw_payload_hash: str
    event_time: datetime
    published_at: datetime
    observed_at: datetime
    available_at: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    effective_at: datetime | None = None
    source_version: str = "1"
    collector_version: str = "1"
    parser_version: str = "1"
    language: str = "en"
    direction: Literal["POSITIVE", "NEGATIVE", "MIXED", "NEUTRAL", "UNKNOWN"] = "UNKNOWN"
    importance: Literal["LOW", "MEDIUM", "HIGH", "MATERIAL"] = "LOW"
    expected_horizon: Literal[
        "INTRADAY", "1_3_SESSIONS", "3_10_SESSIONS", "MEDIUM_TERM", "LONG_TERM", "UNKNOWN"
    ] = "UNKNOWN"
    event_confidence: float = 1.0
    predictive_importance: str = "UNKNOWN"
    quality_status: str = "PASS"
    duplicate_group_id: str | None = None
    correction_of: UUID | None = None
    supersedes: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    collection_origin: Literal["BACKFILLED", "FORWARD_COLLECTED"] = "FORWARD_COLLECTED"
    source_available_at: datetime | None = None
    system_observed_at: datetime | None = None

    @model_validator(mode="after")
    def causal_times(self) -> InformationEvent:
        if self.available_at < self.published_at or self.observed_at < self.published_at:
            raise ValueError("event cannot be available or observed before publication")
        if self.source_available_at is None:
            object.__setattr__(self, "source_available_at", self.published_at)
        if self.system_observed_at is None:
            object.__setattr__(self, "system_observed_at", self.observed_at)
        return self

    @property
    def discovery_latency_seconds(self) -> float:
        return (self.observed_at - self.published_at).total_seconds()

    @property
    def collection_latency_seconds(self) -> float:
        return (self.ingested_at - self.observed_at).total_seconds()


class EntityMatch(FrozenModel):
    status: Literal["MATCHED", "AMBIGUOUS", "UNMATCHED", "MULTI_ENTITY"]
    entity_ids: tuple[str, ...] = ()
    confidence: float
    evidence: tuple[str, ...] = ()


class NoveltyScore(FrozenModel):
    state: Literal["NEW", "UPDATE", "FOLLOW_UP", "DUPLICATE", "RECAP", "CORRECTION", "RUMOUR"]
    score: float
    evidence: tuple[str, ...]


class JobLedgerEntry(FrozenModel):
    job_id: UUID = Field(default_factory=uuid4)
    source_id: str
    mode: CollectionMode
    scheduled_for: datetime
    started_at: datetime
    ended_at: datetime
    status: str
    records_seen: int = 0
    records_new: int = 0
    records_duplicate: int = 0
    records_failed: int = 0
    raw_artifacts: int = 0
    canonical_events: int = 0
    retry_count: int = 0
    error_summary: str | None = None
    collector_version: str = "1"
    code_sha: str = "UNKNOWN"


class IntelligenceSnapshot(FrozenModel):
    entity_id: str
    cutoff: datetime
    events: tuple[InformationEvent, ...]
    source_ids: tuple[str, ...]
    quality_states: tuple[str, ...]
    abstention: Literal["SUFFICIENT", "INSUFFICIENT_INTELLIGENCE"]
    snapshot_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> IntelligenceSnapshot:
        if any(event.available_at > self.cutoff for event in self.events):
            raise ValueError("snapshot contains future intelligence")
        if not self.snapshot_hash:
            object.__setattr__(
                self,
                "snapshot_hash",
                stable_hash(self.model_dump(exclude={"snapshot_hash"}, mode="json")),
            )
        return self


class SourceScorecard(FrozenModel):
    source_id: str
    policy_version: str
    reliability: float
    freshness: float
    coverage: float
    stability: float
    access_risk: float
    cost: float
    entity_resolution_quality: float
    potential_predictive_value: float | None = None
    actual_validated_predictive_value: float | None = None


class IntelligenceIncident(FrozenModel):
    incident_id: UUID = Field(default_factory=uuid4)
    incident_type: Literal[
        "SOURCE_STALE",
        "PARSER_SCHEMA_CHANGE",
        "ENTITY_RESOLUTION_FAILURE_SPIKE",
        "DUPLICATE_RATE_ANOMALY",
        "SOURCE_AUTH_FAILURE",
        "RATE_LIMIT_BREACH",
        "DATA_VOLUME_DROP",
        "SCHEDULER_MISSED_RUN",
        "SNAPSHOT_FAILURE",
        "LLM_PROVIDER_DOWN",
        "LLM_RATE_LIMITED",
        "LLM_SCHEMA_FAILURE_SPIKE",
        "LLM_COST_BUDGET_WARNING",
        "LLM_COST_BUDGET_EXCEEDED",
        "LLM_HALLUCINATION_QUARANTINE",
        "SOURCE_COLLECTION_FAILURE",
        "SOAK_CONFIGURATION_DRIFT",
    ]
    severity: Literal["INFO", "WARNING", "HIGH", "CRITICAL"]
    source_id: str | None = None
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["OPEN", "ACKNOWLEDGED", "RESOLVED"] = "OPEN"
    evidence: dict[str, Any]
    affected_data: tuple[str, ...] = ()
    resolution: str | None = None
    closed_at: datetime | None = None
