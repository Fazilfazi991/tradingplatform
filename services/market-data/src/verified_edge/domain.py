from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QualityStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    WARNING = "WARNING"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SourceCategory(StrEnum):
    MARKET = "MARKET"
    NEWS = "NEWS"
    CORPORATE = "CORPORATE"
    FUNDAMENTAL = "FUNDAMENTAL"
    MACRO = "MACRO"
    SENTIMENT = "SENTIMENT"
    FLOW = "FLOW"
    DERIVATIVES = "DERIVATIVES"
    ALTERNATIVE = "ALTERNATIVE"


class Instrument(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    exchange: str
    segment: str
    symbol: str
    company_name: str | None = None
    isin: str | None = None
    instrument_type: str = "EQUITY"
    tick_size: Decimal | None = None
    listing_status: str = "ACTIVE"
    valid_from: date | None = None
    valid_to: date | None = None
    provider_instrument_key: str | None = None


class RawObservation(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    provider: str
    instrument_id: UUID
    observation_type: str = "OHLCV_DAILY"
    interval: str = "day"
    session_date: date
    observed_at: datetime
    source_timestamp: datetime
    raw_payload: dict[str, Any]
    payload_hash: str
    ingestion_run_id: UUID

    @field_validator("observed_at", "source_timestamp")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class DailyBar(BaseModel):
    model_config = ConfigDict(frozen=True)
    instrument_id: UUID
    symbol: str
    session_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    oi: int | None = None
    provider: str
    raw_observation_id: UUID
    canonical_version: int = 1
    transformation_hash: str
    quality_status: QualityStatus = QualityStatus.ACCEPTED


class QualityEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    severity: Severity
    check_code: str
    instrument_id: UUID | None = None
    session_date: date | None = None
    observed: Any = None
    expected: Any = None
    status: str = "OPEN"
    reason: str


class InformationEvent(BaseModel):
    """Leakage-safe contract shared by all future intelligence sources."""

    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    event_type: str
    source_id: UUID
    value: dict[str, Any]
    event_time: datetime
    published_at: datetime
    observed_at: datetime
    available_at: datetime
    effective_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_artifact_uri: str
    source_version: str
    quality_status: QualityStatus = QualityStatus.ACCEPTED

    @model_validator(mode="after")
    def enforce_information_time(self) -> InformationEvent:
        timestamps = [self.event_time, self.published_at, self.observed_at, self.available_at]
        if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
            raise ValueError("all information timestamps must be timezone-aware")
        if self.available_at < self.published_at:
            raise ValueError("available_at cannot precede published_at")
        if self.observed_at < self.published_at:
            raise ValueError("observed_at cannot precede published_at")
        return self


class UniverseDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str = "NIFTY200_V1"
    version: str = "1"
    membership_source: str
    effective_from: date
    effective_to: date | None = None
    min_prior_sessions: int = 252
    min_median_traded_value_inr: Decimal = Decimal(250000000)
    min_close_inr: Decimal = Decimal(50)
    point_in_time_complete: bool = False
    limitation: str = (
        "Current membership supports ingestion testing only; formal historical research requires "
        "point-in-time membership."
    )
