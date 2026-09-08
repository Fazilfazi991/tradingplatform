from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from research_core.common import stable_hash

from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.forensic_worker import ForensicSemanticProcessor
from intelligence_core.llm_analyzer import (
    AnalyzerTask,
    LLMAnalysisResult,
    LLMProviderAdapter,
    OpenAIResponsesAdapter,
    ProviderConfig,
)
from intelligence_core.models import IntelligenceIncident
from intelligence_core.runtime_forensics import (
    ForensicRuntimeStore,
    StructuredValidationStatus,
    TerminalDisposition,
    TransportStatus,
)
from intelligence_core.worker import JobHandler


def _disabled_handler(reason: str) -> JobHandler:
    def disabled(_job: DurableJob, _now: datetime) -> dict[str, Any]:
        return {
            "status": "DISABLED",
            "reason": reason,
            "prediction_state": "UNCHANGED",
        }

    return disabled


def build_semantic_handler(
    operations: SQLiteOperationsStore,
    forensics: ForensicRuntimeStore,
    processor: ForensicSemanticProcessor,
    *,
    daily_budget_usd: float,
    max_events_per_cycle: int,
    budget_warning_fraction: float = 0.8,
    schema_failure_rate_threshold: float = 0.05,
    schema_failure_minimum_attempts: int = 5,
) -> JobHandler:
    def needs_analysis(event_id: str) -> bool:
        current = forensics.disposition(event_id)
        if current is None:
            return True
        semantic_id, disposition = current
        if disposition not in {
            TerminalDisposition.QUARANTINED,
            TerminalDisposition.FAILED_VALIDATION,
        } or semantic_id is None:
            return False
        prior = forensics.attempts(semantic_id)
        return bool(
            prior
            and prior[-1].grounding_policy_version != processor.grounding_policy_version
        )

    def analyze(_job: DurableJob, now: datetime) -> dict[str, Any]:
        day = now.astimezone(UTC).date()
        spent = sum(
            attempt.estimated_total_cost
            for attempt in forensics.attempts()
            if attempt.completed_at.astimezone(UTC).date() == day
        )
        processed = cache_hits = quarantined = insufficient = 0
        pending = [
            event
            for event in operations.events()
            if event.available_at <= now and needs_analysis(str(event.event_id))
        ][:max_events_per_cycle]
        for event in pending:
            if spent >= daily_budget_usd:
                forensics.set_disposition(
                    event_id=str(event.event_id),
                    semantic_id=None,
                    disposition=TerminalDisposition.NOT_ANALYZED_BY_POLICY,
                    detail={"reason": "DAILY_BUDGET_EXHAUSTED", "state": "PENDING_ANALYSIS"},
                )
                if not operations.has_open_incident("LLM_COST_BUDGET_EXCEEDED"):
                    operations.record_incident(
                        IntelligenceIncident(
                            incident_type="LLM_COST_BUDGET_EXCEEDED",
                            severity="HIGH",
                            evidence={"daily_budget_usd": daily_budget_usd, "spent_usd": spent},
                            affected_data=("semantic-analysis",),
                        )
                    )
                continue
            result = processor.process(
                event_id=str(event.event_id),
                source_id=event.source_id,
                source_artifact_hash=event.raw_payload_hash,
                title=event.title,
                content=event.summary,
                published_at=event.published_at,
                task=AnalyzerTask.EVENT_CLASSIFICATION,
                now=now,
            )
            request_attempts = forensics.attempts(result["semantic_request_id"])
            if request_attempts:
                latest = request_attempts[-1]
                if latest.transport_status is TransportStatus.FAILED:
                    error = (latest.validation_error_code or "").lower()
                    incident_type: Literal["LLM_RATE_LIMITED", "LLM_PROVIDER_DOWN"] = (
                        "LLM_RATE_LIMITED"
                        if latest.http_status_if_available == 429 or "429" in error
                        else "LLM_PROVIDER_DOWN"
                    )
                    if not operations.has_open_incident(incident_type):
                        operations.record_incident(
                            IntelligenceIncident(
                                incident_type=incident_type,
                                severity="HIGH",
                                evidence={
                                    "provider": latest.provider,
                                    "model": latest.model,
                                    "error_class": latest.provider_error_class,
                                },
                                affected_data=(str(event.event_id),),
                            )
                        )
                else:
                    for incident_type in ("LLM_PROVIDER_DOWN", "LLM_RATE_LIMITED"):
                        operations.resolve_open_incidents(
                            incident_type,
                            source_id=None,
                            now=now,
                            resolution="PROVIDER_CALL_RECOVERED",
                        )
            processed += 1
            cache_hits += int(result["cache_hit"])
            disposition = TerminalDisposition(result["disposition"])
            quarantined += int(disposition is TerminalDisposition.QUARANTINED)
            insufficient += int(disposition is TerminalDisposition.INSUFFICIENT_EVIDENCE)
            if disposition is TerminalDisposition.QUARANTINED:
                operations.record_incident(
                    IntelligenceIncident(
                        incident_type="LLM_HALLUCINATION_QUARANTINE",
                        severity="HIGH",
                        source_id=event.source_id,
                        evidence={"canonical_event_id": str(event.event_id)},
                        affected_data=(str(event.event_id),),
                    )
                )
            spent = sum(
                attempt.estimated_total_cost
                for attempt in forensics.attempts()
                if attempt.completed_at.astimezone(UTC).date() == day
            )
            if (
                spent >= daily_budget_usd * budget_warning_fraction
                and spent < daily_budget_usd
                and not operations.has_open_incident("LLM_COST_BUDGET_WARNING")
            ):
                operations.record_incident(
                    IntelligenceIncident(
                        incident_type="LLM_COST_BUDGET_WARNING",
                        severity="WARNING",
                        evidence={
                            "daily_budget_usd": daily_budget_usd,
                            "spent_usd": spent,
                            "warning_fraction": budget_warning_fraction,
                        },
                        affected_data=("semantic-analysis",),
                    )
                )
        schema_attempts = [
            attempt
            for attempt in forensics.attempts()
            if attempt.completed_at.astimezone(UTC).date() == day
            and attempt.transport_status is TransportStatus.SUCCEEDED
        ]
        schema_failures = sum(
            attempt.structured_validation_status is StructuredValidationStatus.FAIL
            for attempt in schema_attempts
        )
        schema_failure_rate = schema_failures / len(schema_attempts) if schema_attempts else 0.0
        if (
            len(schema_attempts) >= schema_failure_minimum_attempts
            and schema_failure_rate > schema_failure_rate_threshold
            and not operations.has_open_incident("LLM_SCHEMA_FAILURE_SPIKE")
        ):
            operations.record_incident(
                IntelligenceIncident(
                    incident_type="LLM_SCHEMA_FAILURE_SPIKE",
                    severity="HIGH",
                    evidence={
                        "failure_rate": schema_failure_rate,
                        "threshold": schema_failure_rate_threshold,
                        "attempts": len(schema_attempts),
                    },
                    affected_data=("semantic-analysis",),
                )
            )
        return {
            "status": "INTERNAL_LIVE_ANALYSIS",
            "processed": processed,
            "cache_hits": cache_hits,
            "quarantined": quarantined,
            "insufficient_evidence": insufficient,
            "pending_seen": len(pending),
            "spent_usd": round(spent, 8),
            "daily_budget_usd": daily_budget_usd,
            "schema_failure_rate": round(schema_failure_rate, 6),
            "prediction_state": "UNCHANGED",
        }

    return analyze


def configured_semantic_handler(
    operations: SQLiteOperationsStore,
    *,
    workspace: str | Path,
    adapter_factory: Callable[[str], LLMProviderAdapter] = lambda key: OpenAIResponsesAdapter(
        api_key=key
    ),
) -> JobHandler:
    if os.getenv("LLM_RUNTIME_ENABLED", "false").lower() != "true":
        return _disabled_handler("LLM_RUNTIME_ENABLED_FALSE")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _disabled_handler("OPENAI_CREDENTIAL_ABSENT")
    root = Path(workspace)
    config = json.loads((root / "config/intelligence-llm-runtime.json").read_text())
    model = os.getenv("OPENAI_MODEL")
    if not model:
        return _disabled_handler("OPENAI_MODEL_ABSENT")
    state_path = root / "data/local/intelligence-forensics.sqlite3"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    forensics = ForensicRuntimeStore(state_path)
    provider = ProviderConfig(
        provider="openai",
        model=model,
        model_version="runtime-configured",
        enabled=True,
        max_output_tokens=600,
        timeout_seconds=45,
        input_cost_per_million=float(config["input_cost_per_million"]),
        output_cost_per_million=float(config["output_cost_per_million"]),
    )
    schema_hash = stable_hash(LLMAnalysisResult.model_json_schema())
    configuration_hash = stable_hash({**config, "model": model})
    processor = ForensicSemanticProcessor(
        store=forensics,
        adapter=adapter_factory(api_key),
        provider_config=provider,
        prompt_version=config["prompt_version"],
        schema_version=config["schema_version"],
        schema_hash=schema_hash,
        routing_version=config["routing_version"],
        configuration_hash=configuration_hash,
        retry_policy_version=config["retry_policy_version"],
        grounding_policy_version=config["grounding_policy_version"],
        max_attempts=int(config["max_attempts"]),
        input_price=float(config["input_cost_per_million"]),
        output_price=float(config["output_cost_per_million"]),
    )
    return build_semantic_handler(
        operations,
        forensics,
        processor,
        daily_budget_usd=float(config["daily_budget_usd"]),
        max_events_per_cycle=int(config["max_events_per_cycle"]),
        budget_warning_fraction=float(config["budget_warning_fraction"]),
        schema_failure_rate_threshold=float(config["schema_failure_rate_threshold"]),
        schema_failure_minimum_attempts=int(config["schema_failure_minimum_attempts"]),
    )
