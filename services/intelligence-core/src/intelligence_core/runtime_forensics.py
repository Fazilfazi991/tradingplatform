from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from research_core.common import stable_hash


class TransportStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    NOT_CALLED_CACHE_HIT = "NOT_CALLED_CACHE_HIT"


class StructuredValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ValidationErrorCategory(StrEnum):
    INVALID_JSON = "INVALID_JSON"
    JSON_PARSE_FAILURE = "JSON_PARSE_FAILURE"
    SCHEMA_SHAPE_MISMATCH = "SCHEMA_SHAPE_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    EXTRA_FIELD = "EXTRA_FIELD"
    ENUM_VIOLATION = "ENUM_VIOLATION"
    WRONG_TYPE = "WRONG_TYPE"
    NULL_NOT_ALLOWED = "NULL_NOT_ALLOWED"
    NUMBER_FORMAT_ERROR = "NUMBER_FORMAT_ERROR"
    UNSUPPORTED_ENTITY = "UNSUPPORTED_ENTITY"
    UNSUPPORTED_NUMERIC_CLAIM = "UNSUPPORTED_NUMERIC_CLAIM"
    UNSUPPORTED_SOURCE_REFERENCE = "UNSUPPORTED_SOURCE_REFERENCE"
    EVIDENCE_GROUNDING_FAILURE = "EVIDENCE_GROUNDING_FAILURE"
    REFUSAL = "REFUSAL"
    TRUNCATED_OUTPUT = "TRUNCATED_OUTPUT"
    EMPTY_OUTPUT = "EMPTY_OUTPUT"
    PROVIDER_FORMAT_MISMATCH = "PROVIDER_FORMAT_MISMATCH"
    OTHER_VALIDATION_ERROR = "OTHER_VALIDATION_ERROR"


class TerminalDisposition(StrEnum):
    SUCCESS = "SUCCESS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED_VALIDATION = "FAILED_VALIDATION"
    QUARANTINED = "QUARANTINED"
    PENDING = "PENDING"
    NOT_ANALYZED_BY_POLICY = "NOT_ANALYZED_BY_POLICY"


class ProviderTransportHealth(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_FAILURE = "AUTH_FAILURE"
    UNKNOWN = "UNKNOWN"


class SemanticValidationHealth(StrEnum):
    HEALTHY = "HEALTHY"
    ELEVATED_FAILURES = "ELEVATED_FAILURES"
    CRITICAL_FAILURE_RATE = "CRITICAL_FAILURE_RATE"
    UNKNOWN = "UNKNOWN"


class LLMAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    attempt_id: UUID = Field(default_factory=uuid4)
    semantic_request_id: str
    canonical_event_id: str
    source_id: str
    source_artifact_hash: str
    semantic_hash: str
    task: str
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    schema_hash: str
    routing_version: str
    configuration_hash: str
    attempt_ordinal: int = Field(ge=1)
    max_attempts: int = Field(ge=1)
    retry_reason: str | None = None
    retry_delay_ms: int = Field(default=0, ge=0)
    retry_policy_version: str
    started_at: datetime
    completed_at: datetime
    latency_ms: float = Field(ge=0)
    transport_status: TransportStatus
    http_status_if_available: int | None = None
    provider_error_class: str | None = None
    provider_request_id_if_safe: str | None = None
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cached_input_tokens_if_exposed: int = Field(default=0, ge=0)
    reasoning_tokens_if_exposed: int = Field(default=0, ge=0)
    estimated_input_cost: float = Field(ge=0)
    estimated_output_cost: float = Field(ge=0)
    estimated_total_cost: float = Field(ge=0)
    structured_validation_status: StructuredValidationStatus
    validation_error_category: ValidationErrorCategory | None = None
    validation_error_code: str | None = None
    sanitized_validation_message: str | None = Field(default=None, max_length=300)
    rejected_response_hash: str | None = None
    rejected_response_length: int | None = Field(default=None, ge=0)
    quarantine_status: str = "NONE"
    cache_write_status: str = "NOT_ATTEMPTED"
    terminal_disposition: TerminalDisposition
    provenance_hash: str


class InvalidSemanticTombstone(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    semantic_request_id: str
    event_id: str
    semantic_hash: str
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    schema_hash: str
    failure_category: ValidationErrorCategory
    attempts_exhausted: int = Field(ge=1)
    created_at: datetime
    expires_at: datetime
    retry_policy_version: str
    reason: str


class CollectionAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    attempt_id: UUID = Field(default_factory=uuid4)
    job_id: str
    source_id: str
    scheduled_for: datetime
    started_at: datetime
    completed_at: datetime
    attempt_ordinal: int = Field(ge=1)
    transport_status: TransportStatus
    http_status: int | None = None
    error_class: str | None = None
    handler_status: str
    parse_status: str
    records_seen: int = Field(default=0, ge=0)
    canonical_events: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    recovered: bool = False
    terminal_job_status: str
    latency_ms: float = Field(ge=0)
    provenance_hash: str


def canonical_semantic_hash(
    *, title: str, content: str, published_at: datetime | None, source_event_id: str
) -> str:
    normalized = " ".join(f"{title} {content}".lower().split())
    return stable_hash(
        {
            "source_event_id": source_event_id,
            "title_content": normalized,
            "published_at": published_at.isoformat() if published_at else None,
        }
    )


def semantic_request_id(*, event_id: str, semantic_hash: str, task: str, policy_hash: str) -> str:
    return stable_hash({"event": event_id, "semantic": semantic_hash, "task": task, "policy": policy_hash})


def validation_category(code: str, *, field_type: str | None = None) -> ValidationErrorCategory:
    value = code.upper()
    mappings = {
        "INVENTED_NUMBER": ValidationErrorCategory.UNSUPPORTED_NUMERIC_CLAIM,
        "UNSUPPORTED_NUMERIC": ValidationErrorCategory.UNSUPPORTED_NUMERIC_CLAIM,
        "WRONG_EVIDENCE_REFERENCE": ValidationErrorCategory.UNSUPPORTED_SOURCE_REFERENCE,
        "MISSING": ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        "EXTRA": ValidationErrorCategory.EXTRA_FIELD,
        "ENUM": ValidationErrorCategory.ENUM_VIOLATION,
        "JSON": ValidationErrorCategory.JSON_PARSE_FAILURE,
        "EMPTY": ValidationErrorCategory.EMPTY_OUTPUT,
        "TRUNCAT": ValidationErrorCategory.TRUNCATED_OUTPUT,
        "REFUSAL": ValidationErrorCategory.REFUSAL,
        "ENTITY": ValidationErrorCategory.UNSUPPORTED_ENTITY,
    }
    for marker, category in mappings.items():
        if marker in value:
            return category
    if field_type == "none_required":
        return ValidationErrorCategory.NULL_NOT_ALLOWED
    if field_type and ("type" in field_type or "parsing" in field_type):
        return ValidationErrorCategory.WRONG_TYPE
    return ValidationErrorCategory.OTHER_VALIDATION_ERROR


def transport_health(attempts: list[LLMAttemptRecord], *, consecutive_limit: int = 3) -> ProviderTransportHealth:
    called = [row for row in attempts if row.transport_status != TransportStatus.NOT_CALLED_CACHE_HIT]
    if not called:
        return ProviderTransportHealth.UNKNOWN
    errors = [row.provider_error_class or "" for row in called]
    if any("AUTH" in value.upper() for value in errors):
        return ProviderTransportHealth.AUTH_FAILURE
    if any("RATE_LIMIT" in value.upper() or "429" in value for value in errors):
        return ProviderTransportHealth.RATE_LIMITED
    consecutive = 0
    for row in reversed(called):
        if row.transport_status == TransportStatus.FAILED:
            consecutive += 1
        else:
            break
    if consecutive >= consecutive_limit:
        return ProviderTransportHealth.UNAVAILABLE
    if any(row.transport_status == TransportStatus.FAILED for row in called):
        return ProviderTransportHealth.DEGRADED
    return ProviderTransportHealth.HEALTHY


def semantic_health(attempts: list[LLMAttemptRecord], *, elevated: float = 0.05, critical: float = 0.20) -> SemanticValidationHealth:
    transported = [row for row in attempts if row.transport_status == TransportStatus.SUCCEEDED]
    if not transported:
        return SemanticValidationHealth.UNKNOWN
    rate = sum(row.structured_validation_status == StructuredValidationStatus.FAIL for row in transported) / len(transported)
    if rate >= critical:
        return SemanticValidationHealth.CRITICAL_FAILURE_RATE
    if rate >= elevated:
        return SemanticValidationHealth.ELEVATED_FAILURES
    return SemanticValidationHealth.HEALTHY


class ForensicRuntimeStore:
    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS llm_attempts (
          attempt_id TEXT PRIMARY KEY, semantic_request_id TEXT NOT NULL,
          canonical_event_id TEXT NOT NULL, occurred_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_llm_attempt_semantic ON llm_attempts(semantic_request_id);
        CREATE TABLE IF NOT EXISTS invalid_semantic_tombstones (
          semantic_request_id TEXT PRIMARY KEY, semantic_hash TEXT NOT NULL,
          expires_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS collection_attempts (
          attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, source_id TEXT NOT NULL,
          scheduled_for TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS event_dispositions (
          canonical_event_id TEXT PRIMARY KEY, semantic_request_id TEXT,
          disposition TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        """)
        self.connection.commit()

    def add_attempt(self, record: LLMAttemptRecord) -> None:
        self.connection.execute(
            "INSERT INTO llm_attempts VALUES(?,?,?,?,?)",
            (str(record.attempt_id), record.semantic_request_id, record.canonical_event_id,
             record.completed_at.isoformat(), record.model_dump_json()),
        )
        self.connection.commit()

    def attempts(self, semantic_id: str | None = None) -> list[LLMAttemptRecord]:
        if semantic_id:
            rows = self.connection.execute(
                "SELECT payload_json FROM llm_attempts WHERE semantic_request_id=? ORDER BY occurred_at", (semantic_id,)
            )
        else:
            rows = self.connection.execute("SELECT payload_json FROM llm_attempts ORDER BY occurred_at")
        return [LLMAttemptRecord.model_validate_json(row[0]) for row in rows]

    def put_tombstone(self, tombstone: InvalidSemanticTombstone) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO invalid_semantic_tombstones VALUES(?,?,?,?)",
            (tombstone.semantic_request_id, tombstone.semantic_hash, tombstone.expires_at.isoformat(), tombstone.model_dump_json()),
        )
        self.connection.commit()

    def active_tombstone(self, semantic_id: str, *, now: datetime) -> InvalidSemanticTombstone | None:
        row = self.connection.execute(
            "SELECT payload_json FROM invalid_semantic_tombstones WHERE semantic_request_id=? AND expires_at>?",
            (semantic_id, now.isoformat()),
        ).fetchone()
        return InvalidSemanticTombstone.model_validate_json(row[0]) if row else None

    def add_collection_attempt(self, record: CollectionAttemptRecord) -> None:
        self.connection.execute(
            "INSERT INTO collection_attempts VALUES(?,?,?,?,?)",
            (str(record.attempt_id), record.job_id, record.source_id, record.scheduled_for.isoformat(), record.model_dump_json()),
        )
        self.connection.commit()

    def set_disposition(self, *, event_id: str, semantic_id: str | None, disposition: TerminalDisposition, detail: dict[str, Any]) -> None:
        payload = {"event_id": event_id, "semantic_request_id": semantic_id, "disposition": disposition, **detail}
        self.connection.execute(
            "INSERT OR REPLACE INTO event_dispositions VALUES(?,?,?,?)",
            (event_id, semantic_id, disposition, json.dumps(payload, sort_keys=True, default=str)),
        )
        self.connection.commit()

    def reconciliation(self) -> dict[str, Any]:
        attempts = self.attempts()
        dispositions = dict(self.connection.execute("SELECT disposition,COUNT(*) FROM event_dispositions GROUP BY disposition"))
        costs: defaultdict[str, float] = defaultdict(float)
        for row in attempts:
            costs["total"] += row.estimated_total_cost
            if row.attempt_ordinal > 1:
                costs["retry_waste"] += row.estimated_total_cost
            if row.structured_validation_status == StructuredValidationStatus.FAIL:
                costs["failed_validation"] += row.estimated_total_cost
        return {
            "attempts": len(attempts),
            "semantic_requests": len({row.semantic_request_id for row in attempts}),
            "validation_categories": dict(Counter(str(row.validation_error_category) for row in attempts if row.validation_error_category)),
            "transport_health": transport_health(attempts),
            "semantic_health": semantic_health(attempts),
            "cost_total_usd": round(costs["total"], 10),
            "retry_waste_usd": round(costs["retry_waste"], 10),
            "failed_validation_cost_usd": round(costs["failed_validation"], 10),
            "event_dispositions": dispositions,
        }

    def close(self) -> None:
        self.connection.close()


def tombstone_for(
    *, semantic_id: str, event_id: str, semantic_hash: str, provider: str, model: str,
    prompt_version: str, schema_version: str, schema_hash: str,
    category: ValidationErrorCategory, attempts: int, retry_policy_version: str,
    now: datetime | None = None, ttl: timedelta = timedelta(hours=24),
) -> InvalidSemanticTombstone:
    created = now or datetime.now(UTC)
    return InvalidSemanticTombstone(
        semantic_request_id=semantic_id, event_id=event_id, semantic_hash=semantic_hash,
        provider=provider, model=model, prompt_version=prompt_version,
        schema_version=schema_version, schema_hash=schema_hash, failure_category=category,
        attempts_exhausted=attempts, created_at=created, expires_at=created + ttl,
        retry_policy_version=retry_policy_version, reason="UNCHANGED_SEMANTIC_INPUT_FAILED_VALIDATION",
    )
