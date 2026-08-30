from datetime import date, timedelta

import pytest
from intelligence_core.fixtures import demo_timeline
from intelligence_core.models import HealthStatus
from intelligence_core.operations import (
    build_daily_archive,
    daily_summary,
    event_priority,
    health_incidents,
    replay_semantic_hash,
)
from intelligence_core.reports import (
    daily_audit_report,
    discovery_report,
    maintenance_report,
    research_proposal,
)
from intelligence_core.universe import UniverseManager, UniverseState


def test_daily_summary_archive_and_deterministic_replay(tmp_path):
    events = demo_timeline()
    day = date(2026, 8, 28)
    health = {"fixture": HealthStatus.HEALTHY}
    summary = daily_summary(day, events, health, [], unresolved_entities=1)
    assert summary["events_collected"] == 6 and summary["duplicates_suppressed"] == 2
    assert summary["prediction"] == "NOT_PRODUCED"
    path = tmp_path / "archive.json"
    first = build_daily_archive(
        day,
        events=events,
        source_health=health,
        job_ids=["j1"],
        incidents=[],
        universe_state={},
        target=path,
    )
    second = build_daily_archive(
        day,
        events=events,
        source_health=health,
        job_ids=["j1"],
        incidents=[],
        universe_state={},
        target=path,
    )
    assert first == second and len(first["manifest_hash"]) == 64
    assert replay_semantic_hash(events) == replay_semantic_hash(list(reversed(events)))
    with pytest.raises(FileExistsError):
        build_daily_archive(
            day,
            events=events,
            source_health=health,
            job_ids=["changed"],
            incidents=[],
            universe_state={},
            target=path,
        )


def test_event_priority_is_not_direction_probability():
    event = demo_timeline()[1]
    assert event_priority(event, reliability=1, novelty=1, entity_relevance=1) == "MATERIAL"
    assert (
        event_priority(
            event.model_copy(update={"quality_status": "BLOCKED"}),
            reliability=1,
            novelty=1,
            entity_relevance=1,
        )
        == "URGENT_REVIEW"
    )


def test_health_incidents():
    assert health_incidents("x", status=HealthStatus.HEALTHY, evidence={}) == []
    assert (
        health_incidents("x", status=HealthStatus.STALE, evidence={})[0].incident_type
        == "SOURCE_STALE"
    )
    assert health_incidents("x", status=HealthStatus.FAILING, evidence={})[0].severity == "HIGH"


def test_universe_stages_changes_without_research_promotion():
    manager = UniverseManager()
    observation = {
        "symbol": "NEWCO",
        "isin": "INE001",
        "legal_name": "New Co",
        "exchange": "NSE",
        "sector": "Industrials",
        "provider": "official",
        "provider_id": "1",
    }
    discovered = manager.detect([observation])
    assert discovered[0].state == UniverseState.DATA_PENDING
    assert manager.coverage()["data_pending"] == 1
    changed = {**observation, "symbol": "NEWCO2"}
    manager.detect([changed])
    assert any(item["type"] == "SYMBOL_CHANGE" for item in manager.changes)
    with pytest.raises(PermissionError):
        manager.transition("INE001", UniverseState.RESEARCH_ELIGIBLE)
    manager.transition("INE001", UniverseState.SUSPENDED)
    assert manager.records["INE001"].state == UniverseState.SUSPENDED


def test_codex_reports_are_proposal_only():
    report = maintenance_report(
        sources=[{"health_status": "FAILING"}], incidents=[], unresolved_entities=[], candidates=[]
    )
    assert "ACTIVATE_SOURCE" in report.prohibited_actions
    candidate = {
        key: "x"
        for key in (
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
        )
    }
    candidate["recommendation"] = "INVESTIGATE"
    assert discovery_report(candidate).report_type == "NEW_SOURCE_CANDIDATE"
    with pytest.raises(ValueError):
        discovery_report({})
    proposal = {
        key: "x"
        for key in (
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
        )
    }
    assert research_proposal(proposal).report_type == "HYPOTHESIS_PROPOSAL"
    assert daily_audit_report(
        health={}, failures=[], entity_issues=[], universe_changes=[], anomalies=[]
    ).report_type.endswith("AUDIT")


def test_forward_backfill_and_latency_are_explicit():
    event = demo_timeline()[0]
    delayed = event.model_copy(
        update={
            "observed_at": event.published_at + timedelta(minutes=27),
            "available_at": event.published_at + timedelta(minutes=27),
            "system_observed_at": event.published_at + timedelta(minutes=27),
        }
    )
    assert delayed.discovery_latency_seconds == 1620
    assert delayed.source_available_at == event.published_at
    backfill = event.model_copy(update={"collection_origin": "BACKFILLED"})
    assert backfill.collection_origin != "FORWARD_COLLECTED"
