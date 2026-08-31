from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from statistics import mean
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from research_core.common import stable_hash


class CostLedgerEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    occurred_at: datetime
    provider: str
    model: str
    task: str
    source_id: str
    canonical_event_id: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_hit: bool = False
    input_cost_usd: float = Field(ge=0)
    output_cost_usd: float = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    latency_ms: float = Field(ge=0)
    error_class: str | None = None
    schema_valid: bool = True
    fallback_attempt: bool = False


def make_cost_entry(
    *,
    occurred_at: datetime,
    provider: str,
    model: str,
    task: str,
    source_id: str,
    canonical_event_id: str,
    input_tokens: int,
    output_tokens: int,
    cache_hit: bool,
    latency_ms: float,
    input_price_per_million: float,
    output_price_per_million: float,
    cached_input_tokens: int = 0,
    cached_input_price_per_million: float = 0,
    error_class: str | None = None,
    schema_valid: bool = True,
    fallback_attempt: bool = False,
) -> CostLedgerEntry:
    uncached_input = max(input_tokens - cached_input_tokens, 0)
    input_cost = (
        uncached_input * input_price_per_million
        + cached_input_tokens * cached_input_price_per_million
    ) / 1_000_000
    output_cost = output_tokens * output_price_per_million / 1_000_000
    return CostLedgerEntry(
        occurred_at=occurred_at,
        provider=provider,
        model=model,
        task=task,
        source_id=source_id,
        canonical_event_id=canonical_event_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_hit=cache_hit,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=input_cost + output_cost,
        latency_ms=latency_ms,
        error_class=error_class,
        schema_valid=schema_valid,
        fallback_attempt=fallback_attempt,
    )


def aggregate_costs(entries: list[CostLedgerEntry], *, report_date: date | None = None) -> dict[str, Any]:
    selected = [entry for entry in entries if report_date is None or entry.occurred_at.date() == report_date]
    totals: defaultdict[str, float] = defaultdict(float)
    by_provider: defaultdict[str, float] = defaultdict(float)
    by_task: defaultdict[str, float] = defaultdict(float)
    by_source: defaultdict[str, float] = defaultdict(float)
    cache_savings = 0.0
    for entry in selected:
        totals["input"] += entry.input_cost_usd
        totals["output"] += entry.output_cost_usd
        totals["total"] += entry.total_cost_usd
        by_provider[entry.provider] += entry.total_cost_usd
        by_task[entry.task] += entry.total_cost_usd
        by_source[entry.source_id] += entry.total_cost_usd
        if entry.cache_hit:
            cache_savings += entry.input_tokens * 0.20 / 1_000_000 + entry.output_tokens * 1.20 / 1_000_000
    return {
        "entries": len(selected),
        "input_cost_usd": round(totals["input"], 10),
        "output_cost_usd": round(totals["output"], 10),
        "total_cost_usd": round(totals["total"], 10),
        "by_provider": {key: round(value, 10) for key, value in sorted(by_provider.items())},
        "by_task": {key: round(value, 10) for key, value in sorted(by_task.items())},
        "by_source": {key: round(value, 10) for key, value in sorted(by_source.items())},
        "cache_savings_usd": round(cache_savings, 10),
    }


class EntityResolutionOutcome(StrEnum):
    CORRECTLY_NON_COMPANY_SPECIFIC = "CORRECTLY_NON_COMPANY_SPECIFIC"
    EXPLICIT_ENTITY_NOT_RESOLVED = "EXPLICIT_ENTITY_NOT_RESOLVED"
    INSUFFICIENT_METADATA = "INSUFFICIENT_METADATA"
    RESOLUTION_BUG = "RESOLUTION_BUG"
    SOURCE_DOES_NOT_SUPPORT_ENTITY = "SOURCE_DOES_NOT_SUPPORT_ENTITY"


class AlertThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)
    version: str
    schema_failure_rate: float = Field(ge=0, le=1)
    consecutive_provider_errors: int = Field(ge=1)
    budget_warning_fraction: float = Field(ge=0, le=1)
    source_stale_seconds: int = Field(ge=1)


class SoakManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    version: str
    started_at: datetime
    target_end_at: datetime
    model: str
    prompt_version: str
    schema_hash: str
    routing_hash: str
    config_hash: str
    code_sha: str
    research_mode: str = "ENGINEERING_FIXTURE"
    runtime_mode: str = "INTERNAL_LIVE"

    def assert_frozen(self, other: SoakManifest) -> None:
        fields = ("model", "prompt_version", "schema_hash", "routing_hash", "config_hash", "code_sha")
        if any(getattr(self, field) != getattr(other, field) for field in fields):
            raise ValueError("SOAK_PROMPT_MODEL_ROUTING_OR_SCHEMA_CHANGED")


class SoakTelemetryStore:
    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS llm_cost_ledger (
          ledger_id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS llm_cache (
          cache_key TEXT PRIMARY KEY, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS soak_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.connection.commit()

    def add_cost(self, entry: CostLedgerEntry) -> None:
        self.connection.execute(
            "INSERT INTO llm_cost_ledger(occurred_at,payload_json) VALUES(?,?)",
            (entry.occurred_at.isoformat(), entry.model_dump_json()),
        )
        self.connection.commit()

    def costs(self) -> list[CostLedgerEntry]:
        return [
            CostLedgerEntry.model_validate_json(row[0])
            for row in self.connection.execute("SELECT payload_json FROM llm_cost_ledger ORDER BY ledger_id")
        ]

    def cache_get(self, key: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT payload_json FROM llm_cache WHERE cache_key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key: str, value: dict[str, Any], now: datetime) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO llm_cache VALUES(?,?,?)",
            (key, json.dumps(value, sort_keys=True), now.isoformat()),
        )
        self.connection.commit()

    def set_metadata(self, key: str, value: str) -> None:
        self.connection.execute("INSERT OR REPLACE INTO soak_metadata VALUES(?,?)", (key, value))
        self.connection.commit()

    def metadata(self) -> dict[str, str]:
        return {row[0]: row[1] for row in self.connection.execute("SELECT key,value FROM soak_metadata")}

    def close(self) -> None:
        self.connection.close()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(round((len(ordered) - 1) * fraction), len(ordered) - 1)]


def runtime_metrics(entries: list[CostLedgerEntry]) -> dict[str, Any]:
    latencies = [entry.latency_ms for entry in entries if not entry.cache_hit]
    errors = Counter(entry.error_class for entry in entries if entry.error_class)
    return {
        "calls": sum(not entry.cache_hit for entry in entries),
        "cache_hits": sum(entry.cache_hit for entry in entries),
        "cache_hit_rate": sum(entry.cache_hit for entry in entries) / len(entries) if entries else 0,
        "input_tokens": sum(entry.input_tokens for entry in entries if not entry.cache_hit),
        "output_tokens": sum(entry.output_tokens for entry in entries if not entry.cache_hit),
        "average_latency_ms": mean(latencies) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 0.50),
        "p95_latency_ms": percentile(latencies, 0.95),
        "provider_errors": dict(errors),
        "invalid_schema_outputs": sum(not entry.schema_valid for entry in entries),
        "fallback_attempts": sum(entry.fallback_attempt for entry in entries),
    }


def budget_state(*, spent_usd: float, ceiling_usd: float, warning_fraction: float) -> str:
    if spent_usd >= ceiling_usd:
        return "EXCEEDED"
    if spent_usd >= ceiling_usd * warning_fraction:
        return "WARNING"
    return "HEALTHY"


def incident_types(
    *,
    entries: list[CostLedgerEntry],
    spent_usd: float,
    budget_usd: float,
    thresholds: AlertThresholds,
) -> tuple[str, ...]:
    incidents: list[str] = []
    if budget_state(
        spent_usd=spent_usd,
        ceiling_usd=budget_usd,
        warning_fraction=thresholds.budget_warning_fraction,
    ) == "WARNING":
        incidents.append("LLM_COST_BUDGET_WARNING")
    if spent_usd >= budget_usd:
        incidents.append("LLM_COST_BUDGET_EXCEEDED")
    failures = [entry for entry in entries if entry.error_class]
    if len(failures) >= thresholds.consecutive_provider_errors:
        incidents.append("LLM_PROVIDER_DOWN")
    if entries and sum(not entry.schema_valid for entry in entries) / len(entries) > thresholds.schema_failure_rate:
        incidents.append("LLM_SCHEMA_FAILURE_SPIKE")
    if any(entry.error_class and "RATE_LIMIT" in entry.error_class for entry in entries):
        incidents.append("LLM_RATE_LIMITED")
    return tuple(incidents)


def manifest_hash(value: Any) -> str:
    return stable_hash(value)


def full_content_access_state(*, retention_status: str, notes: str) -> str:
    text = f"{retention_status} {notes}".upper()
    if "RIGHTS REMAIN SEPARATE" in text or "METADATA" in text:
        return "TITLE_METADATA_ONLY"
    return "REVIEW_REQUIRED"
