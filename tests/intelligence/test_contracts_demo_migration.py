from datetime import UTC, datetime, timedelta
from pathlib import Path

from intelligence_core.contracts import FixtureLLMAnalyzer, MacroObservation
from intelligence_core.demo import main


def test_macro_revision_preserves_original_information_time():
    released = datetime(2026, 1, 1, tzinfo=UTC)
    revised = datetime(2026, 2, 1, tzinfo=UTC)
    observation = MacroObservation(
        available_at=released,
        source_id="fixture",
        quality="PASS",
        provenance={},
        series="CPI",
        period="2025-12",
        original_value=4.5,
        release_time=released,
        revision_value=4.7,
        revision_available_at=revised,
    )
    assert observation.value_as_of(released + timedelta(days=5)) == 4.5
    assert observation.value_as_of(revised) == 4.7


def test_fixture_llm_is_derived_and_returns_unknown_without_evidence():
    analyzer = FixtureLLMAnalyzer()
    now = datetime.now(UTC)
    known = analyzer.analyze("Company earnings released", now=now)
    unknown = analyzer.analyze("No supported classification", now=now)
    assert known.provenance == "DERIVED" and known.evidence_spans
    assert (
        unknown.classification == "UNKNOWN" and unknown.validation_state == "INSUFFICIENT_EVIDENCE"
    )


def test_demo_produces_no_prediction(capsys):
    main()
    output = capsys.readouterr().out
    assert "DEMO_RELIANCE" in output and "Prediction: NOT PRODUCED" in output
    assert "Cutoff: 2026-08-28 14:00 UTC" in output


def test_intelligence_migration_is_append_only_and_indexed():
    root = Path(__file__).resolve().parents[2]
    sql = (root / "infra/migrations/0002_intelligence_acquisition_network.sql").read_text()
    for table in (
        "intelligence_sources",
        "information_events",
        "intelligence_job_ledger",
        "source_candidates",
    ):
        assert f"CREATE TABLE {table}" in sql
    assert "available_at timestamptz NOT NULL" in sql
    assert "UNIQUE (source_id, source_event_id, raw_payload_hash)" in sql
    assert "UPDATE " not in sql.upper()
