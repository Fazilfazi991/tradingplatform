from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Report(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_type: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]
    prohibited_actions: tuple[str, ...] = (
        "ACTIVATE_SOURCE",
        "PUBLISH_PREDICTION",
        "CHANGE_MODEL_GATE",
    )


def maintenance_report(
    *,
    sources: list[dict],
    incidents: list[dict],
    unresolved_entities: list[dict],
    candidates: list[dict],
) -> Report:
    return Report(
        report_type="CODEX_SOURCE_MAINTENANCE",
        payload={
            "failing_sources": [
                s for s in sources if s.get("health_status") in {"FAILING", "DEGRADED", "STALE"}
            ],
            "schema_anomalies": [
                i for i in incidents if i.get("incident_type") == "PARSER_SCHEMA_CHANGE"
            ],
            "new_candidate_sources": candidates,
            "unresolved_entities": unresolved_entities,
            "recommended_actions": [
                "inspect evidence",
                "propose patch on controlled branch",
                "run affected tests",
            ],
        },
    )


def discovery_report(candidate: dict) -> Report:
    required = (
        "name",
        "category",
        "official",
        "access_method",
        "terms",
        "potential_information",
        "potential_predictive_role",
        "source_overlap",
        "expected_cadence",
        "cost",
        "technical_difficulty",
        "legal_status",
        "recommendation",
    )
    missing = [field for field in required if field not in candidate]
    if missing:
        raise ValueError(f"incomplete source proposal: {missing}")
    if candidate["recommendation"] not in {
        "REJECT",
        "INVESTIGATE",
        "FIXTURE_ONLY",
        "APPROVE_FOR_INTERNAL_REVIEW",
    }:
        raise ValueError("invalid source recommendation")
    return Report(report_type="NEW_SOURCE_CANDIDATE", payload=candidate)


def research_proposal(payload: dict) -> Report:
    required = {
        "hypothesis",
        "economic_rationale",
        "data_required",
        "source_availability",
        "possible_target",
        "risk_of_leakage",
        "multiple_testing_family",
        "estimated_sample_size",
        "expected_horizon",
        "recommendation",
    }
    if required - set(payload):
        raise ValueError("incomplete hypothesis proposal")
    return Report(report_type="HYPOTHESIS_PROPOSAL", payload=payload)


def daily_audit_report(
    *, health: dict, failures: list, entity_issues: list, universe_changes: list, anomalies: list
) -> Report:
    return Report(
        report_type="CODEX_DAILY_INTELLIGENCE_AUDIT",
        payload={
            "source_health": health,
            "ingestion_failures": failures,
            "entity_issues": entity_issues,
            "universe_changes": universe_changes,
            "intelligence_anomalies": anomalies,
            "allowed_actions": [
                "CREATE_REPORT",
                "PROPOSE_PATCH",
                "IMPLEMENT_CONTROLLED_PATCH",
                "RUN_TESTS",
            ],
        },
    )
