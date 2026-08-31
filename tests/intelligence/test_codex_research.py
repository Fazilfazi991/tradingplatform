from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from intelligence_core.codex_research import (
    CandidateStatus,
    CodexResearchCandidate,
    CodexResearchIncident,
    NoveltyCandidate,
    ResearchBudget,
    ResearchIncidentType,
    ResearchLedger,
    SourceDiscoveryCandidate,
    missed_run,
    novelty,
    operator_enabled,
    plan_queries,
    title_similarity,
)


def test_operational_incidents_are_bounded() -> None:
    incident = CodexResearchIncident(
        incident_type=ResearchIncidentType.BROWSER_RESEARCH_UNAVAILABLE,
        observed_at=datetime.now(UTC),
        detail="Browser research transport could not be reached",
    )
    assert incident.resolved is False
from intelligence_core.codex_research_fixtures import research_operator_scenarios


def candidate(**updates):
    now = datetime(2026, 8, 31, 10, tzinfo=UTC)
    payload = {
        "discovered_at": now,
        "research_run_id": uuid4(),
        "research_type": "COMPANY_EVENT",
        "scope": "NIFTY_200",
        "entity_id": "INE-DEMO",
        "entity_name": "Demo Industries",
        "symbol": "DEMO",
        "sector": "Industrials",
        "title": "Demo Industries announces official contract update",
        "summary": "A research candidate awaiting standard verification and ingestion.",
        "event_type_candidate": "ORDER_CONTRACT",
        "materiality_candidate": "MEDIUM",
        "novelty_candidate": "NEW",
        "source_url": "https://www.example.com/filing/1",
        "source_domain": "www.example.com",
        "source_type": "PRIMARY_COMPANY",
        "primary_source_url": "https://www.example.com/filing/1",
        "primary_source_status": "FOUND",
        "published_at": now,
        "observed_at": now,
        "available_at": now,
        "verification_status": "UNVERIFIED",
        "duplicate_status": "NEW",
        "codex_reasoning_summary": "The official page appears relevant but is not evidence yet.",
        "codex_confidence": "MEDIUM",
        "source_rights_status": "REVIEW_REQUIRED",
        "recommended_action": "EVIDENCE_ELIGIBILITY_REVIEW",
        "status": "DISCOVERED",
        "provenance": {"operator": "codex", "mode": "exploratory"},
    }
    payload.update(updates)
    return CodexResearchCandidate.model_validate(payload)


def test_candidate_is_strict_causal_hashed_and_non_predictive():
    value = candidate()
    assert value.payload_hash and value.status == CandidateStatus.DISCOVERED
    with pytest.raises(ValueError, match="extra"):
        candidate(unknown_field=True)
    with pytest.raises(ValueError, match="causal"):
        candidate(available_at=value.observed_at - timedelta(seconds=1))
    with pytest.raises(ValueError, match="forbidden"):
        candidate(summary="BUY this security now")


def test_codex_cannot_directly_promote_evidence():
    with pytest.raises(ValueError, match="cannot directly promote"):
        candidate(status="EVIDENCE_ELIGIBLE")


def test_append_only_history_and_safe_transitions(tmp_path):
    ledger = ResearchLedger(tmp_path / "research.sqlite3")
    original = candidate()
    ledger.ingest(original)
    verifying = ledger.transition(original.candidate_id, CandidateStatus.VERIFYING)
    found = ledger.transition(verifying.candidate_id, CandidateStatus.PRIMARY_SOURCE_FOUND)
    assert [row.status for row in ledger.history(original.candidate_id)] == [
        CandidateStatus.DISCOVERED,
        CandidateStatus.VERIFYING,
        CandidateStatus.PRIMARY_SOURCE_FOUND,
    ]
    with pytest.raises(ValueError, match="unsupported"):
        ledger.transition(found.candidate_id, CandidateStatus.DUPLICATE)
    ledger.close()


def test_deterministic_approval_still_hands_off_for_standard_pipeline(tmp_path):
    ledger = ResearchLedger(tmp_path / "research.sqlite3")
    value = candidate()
    ledger.ingest(value)
    value = ledger.transition(value.candidate_id, CandidateStatus.VERIFYING)
    value = ledger.transition(value.candidate_id, CandidateStatus.PRIMARY_SOURCE_FOUND)
    value = ledger.transition(value.candidate_id, CandidateStatus.SOURCE_VERIFIED)
    value = ledger.transition(value.candidate_id, CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW)
    with pytest.raises(ValueError, match="deterministic"):
        ledger.transition(value.candidate_id, CandidateStatus.EVIDENCE_ELIGIBLE)
    approved = ledger.transition(
        value.candidate_id, CandidateStatus.EVIDENCE_ELIGIBLE, deterministic_approval=True
    )
    assert approved.status == CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW
    assert "STANDARD_PIPELINE" in approved.recommended_action
    ledger.close()


def test_dedupe_uses_primary_url_source_entity_title_and_time():
    prior = candidate()
    duplicate = candidate(candidate_id=uuid4(), title="Demo Industries official contract update")
    assert title_similarity(prior.title, duplicate.title) > 0.7
    assert novelty(duplicate, [prior]) == NoveltyCandidate.DUPLICATE
    unrelated = candidate(
        candidate_id=uuid4(),
        entity_id="OTHER",
        title="Central bank liquidity operation",
        source_url="https://www.example.com/other",
        primary_source_url=None,
    )
    assert novelty(unrelated, [prior]) == NoveltyCandidate.NEW


def test_source_discovery_defaults_to_review_required():
    source = SourceDiscoveryCandidate(
        source_name="Official Example Feed",
        official_status=True,
        url="https://www.example.gov/feed",
        data_type="REGULATORY",
        coverage="INDIA",
        frequency="DAILY",
        api_or_feed="RSS",
        rights_notes="Requires review",
        automation_feasibility="TECHNICALLY_FEASIBLE",
        historical_availability="UNKNOWN",
        recommendation="REVIEW",
    )
    assert source.status == "REVIEW_REQUIRED"
    with pytest.raises(ValueError, match="REVIEW_REQUIRED"):
        source.model_copy(update={"status": "ACTIVE"}).no_auto_activation()


def test_query_planner_is_gap_driven_deduplicated_and_bounded():
    result = plan_queries(
        unknown_events=[{"entity": "Demo", "title": "contract update"}] * 3,
        contradictions=[{"topic": "guidance"}],
        incidents=[{"source": "RBI"}],
        budget=ResearchBudget(maximum_queries=3),
    )
    assert len(result) == 3
    assert result[0].endswith("official filing primary source")


def test_feature_flag_defaults_off_and_platform_independence():
    assert not operator_enabled({})
    assert operator_enabled({"CODEX_RESEARCH_OPERATOR_ENABLED": "true"})


def test_missed_run_heartbeat_is_independent():
    expected = datetime(2026, 8, 31, 12, tzinfo=UTC)
    assert missed_run(expected_at=expected, last_completed_at=None, grace=timedelta(minutes=15))
    assert not missed_run(
        expected_at=expected,
        last_completed_at=expected - timedelta(minutes=5),
        grace=timedelta(minutes=15),
    )


def test_fixture_suite_contains_100_deterministic_non_authoritative_scenarios():
    rows = research_operator_scenarios()
    assert len(rows) == 100
    assert len({row["scenario_id"] for row in rows}) == 100
    assert {row["expected_authority"] for row in rows} == {"RESEARCH_CANDIDATE_ONLY"}
    assert {row["expected_prediction_state"] for row in rows} == {"UNCHANGED"}
