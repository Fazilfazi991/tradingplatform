from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from research_core.common import stable_hash


class TaskTier(IntEnum):
    DETERMINISTIC = 0
    ROUTINE = 1
    COMPLEX = 2
    HIGH_MATERIALITY = 3


class ProvenanceMode(StrEnum):
    ALL_FIXTURE = "ALL_FIXTURE"
    PARTIAL_LIVE = "PARTIAL_LIVE"
    ALL_LIVE = "ALL_LIVE"


class LiveEngineStatus(StrEnum):
    LIVE = "LIVE"
    ENGINEERING_ONLY = "ENGINEERING_ONLY"
    INSUFFICIENT = "INSUFFICIENT"
    BLOCKED = "BLOCKED"


PROVIDER_ENVIRONMENTS = {
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL"),
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL"),
    "glm": ("GLM_API_KEY", "GLM_MODEL"),
    "qwen": ("DASHSCOPE_API_KEY", "QWEN_MODEL"),
    "moonshot": ("MOONSHOT_API_KEY", "MOONSHOT_MODEL"),
}

TASK_TIERS = {
    "EVENT_CLASSIFICATION": TaskTier.ROUTINE,
    "TONE": TaskTier.ROUTINE,
    "SUMMARY": TaskTier.ROUTINE,
    "RBI_POLICY_INTERPRETATION": TaskTier.COMPLEX,
    "POLICY_DOCUMENT_SUMMARY": TaskTier.COMPLEX,
    "ENTITY_IMPACT": TaskTier.COMPLEX,
    "MATERIALITY": TaskTier.COMPLEX,
    "FUSION_EXPLANATION": TaskTier.HIGH_MATERIALITY,
}


class BudgetPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    daily_usd: float = Field(default=5.0, ge=0)
    per_task_usd: float = Field(default=0.25, ge=0)
    high_materiality_usd: float = Field(default=1.0, ge=0)


class UsageRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    occurred_at: datetime
    provider: str
    model: str
    task: str
    source_id: str
    canonical_event_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0
    latency_ms: float = 0
    cache_hit: bool = False
    error_class: str | None = None
    fallback: bool = False


@dataclass
class OperationalBudget:
    policy: BudgetPolicy
    records: list[UsageRecord] = field(default_factory=list)

    def authorize(self, *, task: str, estimate_usd: float, now: datetime) -> bool:
        today = sum(
            row.estimated_cost_usd for row in self.records if row.occurred_at.date() == now.date()
        )
        task_total = sum(
            row.estimated_cost_usd
            for row in self.records
            if row.occurred_at.date() == now.date() and row.task == task
        )
        limit = (
            self.policy.high_materiality_usd
            if TASK_TIERS.get(task) == TaskTier.HIGH_MATERIALITY
            else self.policy.per_task_usd
        )
        return today + estimate_usd <= self.policy.daily_usd and task_total + estimate_usd <= limit


def provider_presence(environment: dict[str, str] | None = None) -> dict[str, dict[str, str]]:
    env = environment if environment is not None else os.environ
    return {
        provider: {
            "credential": "PRESENT" if env.get(key_env) else "ABSENT",
            "model": env.get(model_env, "ABSENT"),
        }
        for provider, (key_env, model_env) in PROVIDER_ENVIRONMENTS.items()
    }


def configured_route(
    preferred: tuple[str, ...] = ("openai", "deepseek", "qwen", "glm", "moonshot"),
    environment: dict[str, str] | None = None,
) -> tuple[str, ...]:
    presence = provider_presence(environment)
    return tuple(name for name in preferred if presence[name]["credential"] == "PRESENT")


def semantic_cache_key(
    *,
    input_hash: str,
    task: str,
    prompt_version: str,
    provider: str,
    model: str,
    model_configuration: dict[str, Any],
    schema_version: str,
) -> str:
    return stable_hash(
        {
            "input_hash": input_hash,
            "task": task,
            "prompt_version": prompt_version,
            "provider": provider,
            "model": model,
            "model_configuration": model_configuration,
            "schema_version": schema_version,
        }
    )


def untrusted_evidence_envelope(
    *,
    source_id: str,
    event_id: str,
    artifact_hash: str,
    text: str,
) -> dict[str, Any]:
    return {
        "security_boundary": "UNTRUSTED_DATA_NO_INSTRUCTIONS_NO_TOOLS",
        "source_id": source_id,
        "event_id": event_id,
        "artifact_hash": artifact_hash,
        "text": text,
        "allowed_actions": ("CLASSIFY", "SUMMARIZE", "ABSTAIN"),
        "forbidden_actions": (
            "REQUEST_CREDENTIALS",
            "INVOKE_TOOLS",
            "CHANGE_ROUTING",
            "CHANGE_SOURCE_POLICY",
            "CHANGE_FUSION",
            "CHANGE_RESEARCH_MODE",
            "ACTIVATE_SOURCE",
            "FETCH_URL",
        ),
    }


def provenance_mode(statuses: dict[str, LiveEngineStatus]) -> ProvenanceMode:
    values = set(statuses.values())
    if values == {LiveEngineStatus.LIVE}:
        return ProvenanceMode.ALL_LIVE
    if LiveEngineStatus.LIVE in values:
        return ProvenanceMode.PARTIAL_LIVE
    return ProvenanceMode.ALL_FIXTURE


def partial_live_fusion_guard(statuses: dict[str, LiveEngineStatus]) -> dict[str, Any]:
    mode = provenance_mode(statuses)
    return {
        "mode": mode,
        "label": (
            "PARTIAL LIVE INTELLIGENCE — NOT A LIVE MARKET PREDICTION"
            if mode == ProvenanceMode.PARTIAL_LIVE
            else mode.value
        ),
        "prediction_state": "ABSTAIN" if mode != ProvenanceMode.ALL_LIVE else "UNASSESSED",
        "engines": {key: value.value for key, value in statuses.items()},
    }


def hallucination_incidents(
    output: dict[str, Any],
    *,
    allowed_entities: set[str],
    allowed_numbers: set[str],
    allowed_references: set[str],
    event_id: str,
) -> list[dict[str, str]]:
    checks = {
        "INVENTED_ENTITY": set(output.get("entities", ())) - allowed_entities,
        "INVENTED_NUMBER": {str(value) for value in output.get("numbers", ())} - allowed_numbers,
        "WRONG_SOURCE_REFERENCE": set(output.get("evidence_references", ())) - allowed_references,
    }
    return [
        {"incident_type": kind, "event_id": event_id, "value": value, "action": "QUARANTINE"}
        for kind, values in checks.items()
        for value in sorted(values)
    ]


def daily_live_report(
    *,
    report_date: date,
    live_sources: dict[str, str],
    records: list[UsageRecord],
    events_seen: int,
    canonical_events: int,
    duplicates: int,
    unknown_events: int,
    entity_counts: dict[str, int],
    engine_states: dict[str, LiveEngineStatus],
    incidents: list[dict[str, Any]],
) -> dict[str, Any]:
    total_cost = sum(record.estimated_cost_usd for record in records)
    calls = sum(not record.cache_hit for record in records)
    cache_hits = sum(record.cache_hit for record in records)
    providers = Counter(record.provider for record in records)
    return {
        "date": report_date.isoformat(),
        "label": "INTERNAL LIVE INTELLIGENCE — NO TRADING RECOMMENDATION",
        "live_sources": live_sources,
        "events_seen": events_seen,
        "canonical_events": canonical_events,
        "duplicates": duplicates,
        "llm_calls": calls,
        "llm_cache_hits": cache_hits,
        "estimated_cost_usd": round(total_cost, 8),
        "cost_by_provider": dict(providers),
        "unknown_rate": unknown_events / canonical_events if canonical_events else 1.0,
        "entity_resolution": entity_counts,
        "provenance": partial_live_fusion_guard(engine_states),
        "incidents": incidents,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def benchmark_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep quality, grounding, latency, and cost separate rather than naming one winner."""
    by_provider: dict[str, dict[str, Any]] = {}
    for provider in sorted({str(row["provider"]) for row in rows}):
        group = [row for row in rows if row["provider"] == provider]
        count = len(group)
        by_provider[provider] = {
            "cases": count,
            "schema_success_rate": sum(bool(row.get("schema_success")) for row in group) / count,
            "classification_correct_rate": sum(
                bool(row.get("classification_correct")) for row in group
            )
            / count,
            "abstention_correct_rate": sum(bool(row.get("abstention_correct")) for row in group)
            / count,
            "grounding_rate": sum(bool(row.get("grounded")) for row in group) / count,
            "unsupported_claim_rate": sum(bool(row.get("unsupported_claim")) for row in group)
            / count,
            "mean_latency_ms": sum(float(row.get("latency_ms", 0)) for row in group) / count,
            "estimated_cost_usd": sum(float(row.get("estimated_cost_usd", 0)) for row in group),
        }
    return {
        "providers": by_provider,
        "selection_policy": "NO_SINGLE_AGGREGATE_WINNER",
        "routing_recommendation": (
            "REVIEW_BY_TASK" if rows else "INSUFFICIENT_CONFIGURED_PROVIDER_RESULTS"
        ),
    }
