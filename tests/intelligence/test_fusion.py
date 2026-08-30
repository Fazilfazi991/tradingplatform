from datetime import UTC, datetime, timedelta

import pytest
from intelligence_core.fusion import (
    DependencyType,
    EngineStatus,
    EvidenceOrientation,
    FusionState,
    SpecialistEvidenceOutput,
    agreement,
    dependency_graph,
    dominance_warning,
    engine_removal_analysis,
    evidence_quality,
    fuse_evidence,
    fuse_specialist_outputs,
    fusion_qa,
    sensitivity_analysis,
)
from intelligence_core.fusion_fixtures import fusion_fixture_cases, null_fusion_fixture

NOW = datetime(2026, 8, 30, 12, tzinfo=UTC)


def output(engine="TECHNICAL", orientation="SUPPORTIVE", **updates):
    values = {"engine_id": engine, "engine_family": engine, "engine_version": "1",
              "scope": "ENTITY:RELIANCE", "entity_id": "RELIANCE", "as_of": NOW,
              "horizon": "1D", "status": EngineStatus.AVAILABLE,
              "evidence_orientation": EvidenceOrientation(orientation), "certainty": 0.8,
              "data_quality": "PASS", "freshness": 1, "coverage": 0.8,
              "supporting_evidence": (f"{engine}-support",), "adverse_evidence": (),
              "provenance": {"observation": engine}, "snapshot_hash": f"snapshot-{engine}",
              "source_quality": 0.8, "causal_integrity": 1, "sample_adequacy": 0.8}
    if EvidenceOrientation(orientation) in {EvidenceOrientation.ADVERSE,
                                            EvidenceOrientation.STRONGLY_ADVERSE}:
        values["supporting_evidence"] = ()
        values["adverse_evidence"] = (f"{engine}-adverse",)
    values.update(updates)
    return SpecialistEvidenceOutput(**values)


def seven(**overrides):
    engines = ("TECHNICAL", "HISTORICAL", "NEWS_EVENT", "MACRO_GLOBAL", "FUNDAMENTAL",
               "PSYCHOLOGY", "FLOW_DERIVATIVES")
    return tuple(output(engine, **overrides.get(engine, {})) for engine in engines)


def test_unified_contract_hashes_and_unavailable_is_not_neutral():
    assert output().payload_hash
    with pytest.raises(ValueError, match="unavailable"):
        output(status=EngineStatus.INSUFFICIENT, orientation="NEUTRAL")


def test_quality_is_independent_from_orientation_and_stale_is_very_low():
    assert evidence_quality(output("A", "SUPPORTIVE")).tier == "HIGH"
    assert evidence_quality(output("B", "ADVERSE")).tier == "HIGH"
    assert evidence_quality(output(status=EngineStatus.STALE, freshness=0)).tier == "VERY_LOW"


def test_dependency_graph_detects_shared_provenance_and_discounts():
    news = output("NEWS_EVENT", cluster_ids=("rbi-1",), source_ids=("rbi",))
    psychology = output("PSYCHOLOGY", cluster_ids=("rbi-1",), source_ids=("rbi",),
                        event_ids=("event-1",))
    macro = output("MACRO_GLOBAL", cluster_ids=("rbi-1",), source_ids=("rbi",),
                   event_ids=("event-1",))
    graph = dependency_graph((news, psychology, macro))
    assert any(x.dependency_type == DependencyType.HIGHLY_OVERLAPPING for x in graph.dependencies)
    assert graph.factor_for("MACRO_GLOBAL") == 0.35


def test_agreement_is_not_probability_and_reports_quality_conflict():
    items = (output("TECHNICAL", "SUPPORTIVE"), output("MACRO_GLOBAL", "ADVERSE"))
    result = agreement(items)
    assert result.state == "STRONG_CONFLICT"
    assert result.high_quality_supportive == ("TECHNICAL",)
    assert result.high_quality_adverse == ("MACRO_GLOBAL",)


def test_missing_engines_are_insufficient_and_excessive_missing_abstains():
    result = fuse_specialist_outputs((output("TECHNICAL"), output("NEWS_EVENT")))
    assert result.fusion_state == FusionState.ABSTAIN
    assert "EXCESSIVE_MISSING_ENGINES" in result.abstention
    assert "return probability" in result.explanation["not"]


def test_quality_precedence_beats_low_quality_majority():
    low_support = tuple(output(f"LOW-{i}", source_quality=0.1, certainty=0.2,
                               coverage=0.2, sample_adequacy=0.1) for i in range(5))
    high_adverse = (output("MACRO_GLOBAL", "ADVERSE"), output("FUNDAMENTAL", "ADVERSE"))
    result = fuse_specialist_outputs((*low_support, *high_adverse))
    assert result.fusion_state in {FusionState.CONFLICTED, FusionState.ABSTAIN}
    assert result.fusion_state != FusionState.SUPPORTIVE


def test_strong_high_quality_directional_conflict_remains_visible_and_abstains():
    items = seven(MACRO_GLOBAL={"orientation": "ADVERSE"},
                  FLOW_DERIVATIVES={"orientation": "ADVERSE"})
    result = fuse_specialist_outputs(items)
    assert result.fusion_state == FusionState.ABSTAIN
    assert "STRONG_ENGINE_CONFLICT" in result.abstention
    assert result.contradictions and result.uncertainty.state == "VERY_HIGH"


def test_causal_cutoff_scope_and_horizon_fail_closed():
    with pytest.raises(ValueError, match="after cutoff"):
        fuse_specialist_outputs((output(as_of=NOW + timedelta(minutes=1)), output("NEWS_EVENT")),
                                cutoff=NOW)
    with pytest.raises(ValueError, match="scope and horizon"):
        fuse_specialist_outputs((output(), output("NEWS_EVENT", horizon="5D")))


def test_replay_is_semantically_and_hash_identical():
    first = fuse_specialist_outputs(seven())
    second = fuse_specialist_outputs(seven())
    assert first.fusion_state == second.fusion_state
    assert first.payload_hash == second.payload_hash


def test_removal_dominance_and_sensitivity_are_exposed():
    snapshot = fuse_specialist_outputs((output("TECHNICAL"), output("HISTORICAL"),
                                        output("NEWS_EVENT")))
    removal = engine_removal_analysis(snapshot)
    sensitivity = sensitivity_analysis(snapshot)
    assert set(removal) == {"ORIGINAL", "WITHOUT_TECHNICAL", "WITHOUT_HISTORICAL",
                            "WITHOUT_NEWS_EVENT"}
    assert {"FIRST_ENGINE_QUALITY_DOWNGRADE", "FIRST_ENGINE_STALE",
            "FIRST_ENGINE_MISSING"} <= set(sensitivity)
    assert dominance_warning(snapshot) is None or dominance_warning(snapshot).startswith("ENGINE_DOMINANCE")


def test_api_selects_same_cutoff_scope_horizon_and_rejects_empty_selection():
    outputs = (*seven(), output("OTHER", as_of=NOW + timedelta(hours=1)))
    snapshot = fuse_evidence("ENTITY:RELIANCE", NOW, "1D", outputs)
    assert len(snapshot.engine_snapshots) == 7
    with pytest.raises(ValueError, match="requires"):
        fuse_evidence("MARKET:INDIA", NOW, "1D", outputs)


def test_fusion_qa_and_fixture_families_are_conservative():
    supportive = fuse_specialist_outputs(seven())
    conflict = fuse_specialist_outputs(seven(MACRO_GLOBAL={"orientation": "ADVERSE"}))
    metrics = fusion_qa([supportive, conflict])
    assert metrics["fusion_count"] == 2 and metrics["contribution_count"] == 14
    fixtures, null = fusion_fixture_cases(), null_fusion_fixture()
    assert len(fixtures) == 320 and len(null) == 300
    assert {x["case"] for x in fixtures} >= {"correlated news psychology macro", "stale news",
                                             "multiple low-quality vs one high-quality"}
    counts = {state: sum(x["orientation"] == state for x in null)
              for state in {x["orientation"] for x in null}}
    assert set(counts.values()) == {60}
