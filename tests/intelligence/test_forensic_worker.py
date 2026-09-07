from datetime import UTC, datetime
from uuid import UUID

from intelligence_core.collectors import RawArtifact
from intelligence_core.durable import DurableJob, SQLiteOperationsStore
from intelligence_core.forensic_worker import ForensicSemanticProcessor
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
