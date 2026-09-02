from datetime import UTC, datetime

from intelligence_core.forensic_worker import ForensicSemanticProcessor
from intelligence_core.llm_analyzer import AnalyzerTask, ProviderConfig, ProviderResponse
from intelligence_core.runtime_forensics import ForensicRuntimeStore, TerminalDisposition

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
