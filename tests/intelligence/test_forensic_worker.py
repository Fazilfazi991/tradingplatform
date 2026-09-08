from datetime import UTC, datetime
from uuid import UUID

import pytest
from intelligence_core.collectors import RawArtifact
from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.forensic_worker import (
    ForensicSemanticProcessor,
    validate_summary_numbers,
    visible_source_text,
)
from intelligence_core.llm_analyzer import AnalyzerTask, ProviderConfig, ProviderResponse
from intelligence_core.models import EventType, InformationEvent
from intelligence_core.runtime_forensics import ForensicRuntimeStore, TerminalDisposition
from intelligence_core.semantic_runtime import build_semantic_handler

from scripts.run_24h_live_intelligence_soak import acquire_awake_lease, build_manifest

NOW = datetime(2026, 9, 2, tzinfo=UTC)


class QueueAdapter:
    provider = "openai"

    def __init__(self, outputs: list[dict]) -> None:
        self.outputs = outputs
        self.calls = 0

    def generate_structured(self, **_kwargs) -> ProviderResponse:
        output = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return ProviderResponse(
            output=output,
            input_tokens=100,
            output_tokens=20,
            response_hash=f"response-{self.calls}",
            response_length=200,
        )


def result(summary: str = "Policy remains unchanged.", status: str = "SUCCESS") -> dict:
    return {
        "event_type": "RBI_POLICY",
        "direction": "NEUTRAL",
        "materiality": "MEDIUM",
        "confirmation_state": "OFFICIAL_CONFIRMED",
        "certainty": 0.8,
        "summary": summary,
        "evidence_references": [],
        "status": status,
    }


def processor(tmp_path, outputs: list[dict]):
    store = ForensicRuntimeStore(tmp_path / "worker.sqlite3")
    adapter = QueueAdapter(outputs)
    worker = ForensicSemanticProcessor(
        store=store,
        adapter=adapter,
        provider_config=ProviderConfig(
            provider="openai", model="gpt-5.6-luna", model_version="test-frozen"
        ),
        prompt_version="p1",
        schema_version="s1",
        schema_hash="schema",
        routing_version="route",
        configuration_hash="config",
    )
    return store, adapter, worker


def invoke(worker: ForensicSemanticProcessor, *, artifact: str = "artifact-1"):
    return worker.process(
        event_id="rbi:event-1",
        source_id="rbi",
        source_artifact_hash=artifact,
        title="RBI policy update",
        content="Policy remains unchanged.",
        published_at=NOW,
        task=AnalyzerTask.RBI_POLICY_INTERPRETATION,
        now=NOW,
    )


def test_success_is_cached_by_semantics_not_wrapper_artifact(tmp_path):
    store, adapter, worker = processor(tmp_path, [result()])
    assert invoke(worker)["disposition"] == TerminalDisposition.SUCCESS
    cached = invoke(worker, artifact="different-feed-wrapper")
    assert cached["cache_hit"] is True
    assert adapter.calls == 1
    assert store.reconciliation()["attempts"] == 1
    store.close()


def test_paid_invalid_responses_are_ledgered_then_tombstoned(tmp_path):
    store, adapter, worker = processor(tmp_path, [result("Rates moved to 99%.")])
    outcome = invoke(worker)
    assert outcome["disposition"] == TerminalDisposition.QUARANTINED
    assert adapter.calls == 2
    rows = store.attempts(outcome["semantic_request_id"])
    assert len(rows) == 2
    assert all(row.input_tokens == 100 and row.output_tokens == 20 for row in rows)
    assert all(row.rejected_response_hash for row in rows)
    assert rows[-1].claim_field == "summary"
    again = invoke(worker)
    assert again["tombstone_hit"] is True and adapter.calls == 2
    store.close()


def test_numeric_grounding_accepts_only_safe_formatting_equivalence():
    source = "Dates September 08 and 09. Amount ₹ -2,64,000.00 crore and rate 5.24%."
    validate_summary_numbers(
        "Dates 8 and 9; amount ₹ -264000 crore and rate 5.240%.", source
    )


def test_numeric_grounding_preserves_sign_percent_and_magnitude():
    source = "Amount -2,45,922.00 and rate 5.24%."
    for unsupported in (
        "Amount 245922.",
        "Rate 5.24.",
        "Rate 5.25%.",
        "Amount -245923.",
        "Amount -245922 crore.",
    ):
        with pytest.raises(ValueError, match="INVENTED_NUMBER"):
            validate_summary_numbers(unsupported, source)


def test_html_attributes_scripts_and_styles_are_not_numeric_evidence():
    source = '<table width="100" border="7"><style>.x{width:88px}</style><script>99</script><td>8</td></table>'
    assert visible_source_text(source) == "8"
    validate_summary_numbers("Value 08.", visible_source_text(source))
    for unsupported in ("Value 100.", "Value 7.", "Value 88.", "Value 99."):
        with pytest.raises(ValueError, match="INVENTED_NUMBER"):
            validate_summary_numbers(unsupported, visible_source_text(source))
    escaped = "Visible &lt;script&gt;99&lt;/script&gt; evidence"
    assert visible_source_text(escaped) == "Visible <script>99</script> evidence"
    validate_summary_numbers("Value 99.", visible_source_text(escaped))


def test_grounding_policy_is_part_of_attempt_and_semantic_identity(tmp_path):
    first_store = ForensicRuntimeStore(tmp_path / "first.sqlite3")
    second_store = ForensicRuntimeStore(tmp_path / "second.sqlite3")
    config = ProviderConfig(provider="openai", model="gpt-5.6-luna", model_version="frozen")
    first = ForensicSemanticProcessor(
        store=first_store,
        adapter=QueueAdapter([result()]),
        provider_config=config,
        prompt_version="p2",
        schema_version="s1",
        schema_hash="schema",
        routing_version="route",
        configuration_hash="config",
        grounding_policy_version="grounding-v1",
    )
    second = ForensicSemanticProcessor(
        store=second_store,
        adapter=QueueAdapter([result()]),
        provider_config=config,
        prompt_version="p2",
        schema_version="s1",
        schema_hash="schema",
        routing_version="route",
        configuration_hash="config",
        grounding_policy_version="grounding-v2",
    )
    first_result, second_result = invoke(first), invoke(second)
    assert first_result["semantic_request_id"] != second_result["semantic_request_id"]
    assert first_store.attempts()[0].grounding_policy_version == "grounding-v1"
    assert second_store.attempts()[0].grounding_policy_version == "grounding-v2"
    first_store.close()
    second_store.close()


def test_disposition_history_is_append_only_and_schema_reopen_is_idempotent(tmp_path):
    path = tmp_path / "history.sqlite3"
    store = ForensicRuntimeStore(path)
    store.set_disposition(
        event_id="event-1", semantic_id="semantic-v1",
        disposition=TerminalDisposition.QUARANTINED, detail={"policy": "v1"},
    )
    store.set_disposition(
        event_id="event-1", semantic_id="semantic-v2",
        disposition=TerminalDisposition.SUCCESS, detail={"policy": "v2"},
    )
    assert store.connection.execute(
        "SELECT COUNT(*) FROM event_disposition_history"
    ).fetchone()[0] == 2
    store.close()
    reopened = ForensicRuntimeStore(path)
    assert reopened.connection.execute(
        "SELECT COUNT(*) FROM event_disposition_history"
    ).fetchone()[0] == 2
    assert reopened.disposition("event-1") == ("semantic-v2", TerminalDisposition.SUCCESS)
    reopened.close()


def test_revised_policy_boundedly_reevaluates_only_prior_failures(tmp_path):
    runtime_now = datetime.now(UTC)
    operations = SQLiteOperationsStore(tmp_path / "operations.sqlite3")
    source_event = InformationEvent(
        event_id=UUID(int=8),
        entity_id=None,
        entity_type="REGULATOR",
        source_id="rbi-rss",
        source_event_id="policy-8",
        event_type=EventType.CENTRAL_BANK,
        title="RBI update dated September 08",
        summary="The notice was published on September 08.",
        raw_artifact_uri="artifact://policy-8",
        raw_payload_hash="artifact-8",
        event_time=NOW,
        published_at=NOW,
        observed_at=NOW,
        available_at=NOW,
        ingested_at=NOW,
    )
    operations.persist_collection(
        RawArtifact("rbi-rss", "artifact://policy-8", "text/plain", b"policy", NOW),
        [source_event],
    )
    store = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    config = ProviderConfig(provider="openai", model="gpt-5.6-luna", model_version="frozen")
    old = ForensicSemanticProcessor(
        store=store,
        adapter=QueueAdapter([result("Unsupported 99.")]),
        provider_config=config,
        prompt_version="p1",
        schema_version="s1",
        schema_hash="schema",
        routing_version="route",
        configuration_hash="config",
        grounding_policy_version="grounding-v1",
    )
    old.process(
        event_id=str(source_event.event_id), source_id=source_event.source_id,
        source_artifact_hash=source_event.raw_payload_hash, title=source_event.title,
        content=source_event.summary, published_at=source_event.published_at,
        task=AnalyzerTask.EVENT_CLASSIFICATION, now=runtime_now,
    )
    revised_adapter = QueueAdapter([result("Published on September 8.")])
    revised = ForensicSemanticProcessor(
        store=store,
        adapter=revised_adapter,
        provider_config=config,
        prompt_version="p2",
        schema_version="s1",
        schema_hash="schema",
        routing_version="route",
        configuration_hash="config-v2",
        grounding_policy_version="grounding-v2",
    )
    handler = build_semantic_handler(
        operations, store, revised, daily_budget_usd=1, max_events_per_cycle=1
    )
    outcome = handler(
        DurableJob("llm-event-analysis", "INTERVAL", None, 900, None, None, NOW, "1"),
        runtime_now,
    )
    assert outcome["processed"] == 1
    assert revised_adapter.calls == 1
    assert len(store.attempts()) == 3
    assert store.disposition(str(source_event.event_id))[1] is TerminalDisposition.SUCCESS
    operations.close()
    store.close()


def test_validation_retry_can_recover_without_false_provider_failure(tmp_path):
    store, adapter, worker = processor(tmp_path, [{"bad": "shape"}, result()])
    outcome = invoke(worker)
    state = store.reconciliation()
    assert outcome["disposition"] == TerminalDisposition.SUCCESS
    assert adapter.calls == 2
    assert state["transport_health"] == "HEALTHY"
    assert state["retry_waste_usd"] > 0
    store.close()


def test_production_manifest_is_stable_across_dynamic_catalog_timestamps(monkeypatch):
    monkeypatch.setattr("scripts.run_24h_live_intelligence_soak.current_sha", lambda: "abc123")
    config = {
        "version": "test",
        "target_duration_hours": 24,
        "budget": {"daily_usd": 0.25},
    }
    first = build_manifest(config, now=NOW, model="gpt-5.6-luna", soak_id="soak-1")
    second = build_manifest(config, now=NOW, model="gpt-5.6-luna", soak_id="soak-1")
    first.assert_frozen(second)
    assert first.soak_manifest_hash == second.soak_manifest_hash


def test_local_soak_acquires_platform_awake_lease():
    import os

    assert acquire_awake_lease() is (os.name == "nt")


def test_manifest_accepts_explicit_frozen_sha_without_git(monkeypatch):
    frozen = "a" * 40
    monkeypatch.setenv("QUALIFYING_CODE_SHA", frozen)
    monkeypatch.setattr(
        "scripts.run_24h_live_intelligence_soak.subprocess.check_output",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("git must not run")),
    )
    config = {"version": "test", "target_duration_hours": 24, "budget": {"daily_usd": 1}}
    assert (
        build_manifest(config, now=NOW, model="gpt-5.6-luna", soak_id="scheduled").code_sha
        == frozen
    )


def test_scheduled_semantic_runtime_alerts_on_budget_and_schema_failures(tmp_path):
    runtime_now = datetime.now(UTC)
    operations = SQLiteOperationsStore(tmp_path / "operations.sqlite3")
    source_event = InformationEvent(
        event_id=UUID(int=7),
        entity_id=None,
        entity_type="REGULATOR",
        source_id="rbi-rss",
        source_event_id="policy-7",
        event_type=EventType.CENTRAL_BANK,
        title="RBI policy update",
        summary="Policy remains unchanged.",
        raw_artifact_uri="artifact://policy-7",
        raw_payload_hash="artifact-7",
        event_time=NOW,
        published_at=NOW,
        observed_at=NOW,
        available_at=NOW,
        ingested_at=NOW,
    )
    operations.persist_collection(
        RawArtifact("rbi-rss", "artifact://policy-7", "text/plain", b"policy", NOW),
        [source_event],
    )
    forensic_store, adapter, semantic_processor = processor(
        tmp_path, [result("Rates moved to 99%.")]
    )
    handler = build_semantic_handler(
        operations,
        forensic_store,
        semantic_processor,
        daily_budget_usd=0.0001,
        max_events_per_cycle=1,
        budget_warning_fraction=0.5,
        schema_failure_rate_threshold=0.1,
        schema_failure_minimum_attempts=1,
    )
    job = DurableJob("llm-event-analysis", "INTERVAL", None, 900, None, None, NOW, "1")
    outcome = handler(job, runtime_now)
    incident_types = {row["incident_type"] for row in operations.incidents()}
    assert outcome["quarantined"] == 1
    assert outcome["schema_failure_rate"] == 1.0
    assert adapter.calls == 2
    assert "LLM_HALLUCINATION_QUARANTINE" in incident_types
    assert "LLM_COST_BUDGET_WARNING" in incident_types
    assert "LLM_SCHEMA_FAILURE_SPIKE" in incident_types
    operations.close()
    forensic_store.close()
