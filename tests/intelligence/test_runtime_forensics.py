from datetime import UTC, datetime, timedelta

from intelligence_core.runtime_forensics import (
    CollectionAttemptRecord,
    ForensicRuntimeStore,
    LLMAttemptRecord,
    ProviderTransportHealth,
    SemanticValidationHealth,
    StructuredValidationStatus,
    TerminalDisposition,
    TransportStatus,
    ValidationErrorCategory,
    canonical_semantic_hash,
    semantic_health,
    semantic_request_id,
    tombstone_for,
    transport_health,
    validation_category,
)

NOW = datetime(2026, 9, 1, tzinfo=UTC)


def attempt(**updates) -> LLMAttemptRecord:
    payload = {
        "semantic_request_id": "semantic-1",
        "canonical_event_id": "event-1",
        "source_id": "rbi",
        "source_artifact_hash": "artifact-1",
        "semantic_hash": "meaning-1",
        "task": "EVENT_CLASSIFICATION",
        "provider": "openai",
        "model": "gpt-5.6-luna",
        "prompt_version": "p1",
        "schema_version": "s1",
        "schema_hash": "schema-hash",
        "routing_version": "route-1",
        "configuration_hash": "config-1",
        "attempt_ordinal": 1,
        "max_attempts": 2,
        "retry_policy_version": "bounded-v1",
        "started_at": NOW,
        "completed_at": NOW + timedelta(seconds=1),
        "latency_ms": 1000,
        "transport_status": TransportStatus.SUCCEEDED,
        "input_tokens": 1000,
        "output_tokens": 100,
        "estimated_input_cost": 0.0002,
        "estimated_output_cost": 0.00012,
        "estimated_total_cost": 0.00032,
        "structured_validation_status": StructuredValidationStatus.PASS,
        "terminal_disposition": TerminalDisposition.SUCCESS,
        "provenance_hash": "provenance-1",
    }
    payload.update(updates)
    return LLMAttemptRecord.model_validate(payload)


def test_failed_validation_keeps_tokens_cost_hash_and_retry_ordinal():
    row = attempt(
        attempt_ordinal=2,
        structured_validation_status="FAIL",
        validation_error_category="UNSUPPORTED_NUMERIC_CLAIM",
        rejected_response_hash="sha256-value",
        rejected_response_length=317,
        quarantine_status="QUARANTINED",
        cache_write_status="TOMBSTONE_ONLY",
        terminal_disposition="QUARANTINED",
    )
    assert row.input_tokens == 1000 and row.estimated_total_cost == 0.00032
    assert row.attempt_ordinal == 2 and row.rejected_response_hash == "sha256-value"


def test_semantic_identity_ignores_feed_wrapper_hash():
    first = canonical_semantic_hash(
        title="RBI policy update", content="Official content", published_at=NOW, source_event_id="rbi:1"
    )
    second = canonical_semantic_hash(
        title=" RBI  policy update ", content="Official   content", published_at=NOW, source_event_id="rbi:1"
    )
    assert first == second
    assert semantic_request_id(event_id="rbi:1", semantic_hash=first, task="EVENT", policy_hash="p") == semantic_request_id(
        event_id="rbi:1", semantic_hash=second, task="EVENT", policy_hash="p"
    )


def test_validation_taxonomy_is_explicit():
    assert validation_category("INVENTED_NUMBER_QUARANTINED") == ValidationErrorCategory.UNSUPPORTED_NUMERIC_CLAIM
    assert validation_category("WRONG_EVIDENCE_REFERENCE") == ValidationErrorCategory.UNSUPPORTED_SOURCE_REFERENCE
    assert validation_category("missing", field_type="missing") == ValidationErrorCategory.MISSING_REQUIRED_FIELD


def test_schema_failures_never_trigger_provider_down():
    schema_failures = [
        attempt(
            structured_validation_status="FAIL",
            validation_error_category="ENUM_VIOLATION",
            terminal_disposition="FAILED_VALIDATION",
        )
        for _ in range(4)
    ]
    assert transport_health(schema_failures) == ProviderTransportHealth.HEALTHY
    assert semantic_health(schema_failures) == SemanticValidationHealth.CRITICAL_FAILURE_RATE


def test_cost_reconciliation_counts_failed_retry_and_success(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    store.add_attempt(attempt())
    store.add_attempt(
        attempt(
            attempt_ordinal=2,
            structured_validation_status="FAIL",
            validation_error_category="ENUM_VIOLATION",
            terminal_disposition="FAILED_VALIDATION",
        )
    )
    store.add_attempt(attempt(attempt_ordinal=3, max_attempts=3))
    totals = store.reconciliation()
    assert totals["attempts"] == 3
    assert totals["cost_total_usd"] == 0.00096
    assert totals["failed_validation_cost_usd"] == 0.00032
    assert totals["retry_waste_usd"] == 0.00064
    store.close()


def test_invalid_tombstone_prevents_cross_cycle_retry(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    tombstone = tombstone_for(
        semantic_id="semantic-1", event_id="event-1", semantic_hash="meaning-1",
        provider="openai", model="gpt-5.6-luna", prompt_version="p1",
        schema_version="s1", schema_hash="h1", category=ValidationErrorCategory.ENUM_VIOLATION,
        attempts=2, retry_policy_version="bounded-v1", now=NOW,
    )
    store.put_tombstone(tombstone)
    assert store.active_tombstone("semantic-1", now=NOW + timedelta(hours=1)) == tombstone
    assert store.active_tombstone("semantic-1", now=NOW + timedelta(days=2)) is None
    store.close()


def test_collection_attempt_preserves_recovered_failure(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "forensics.sqlite3")
    row = CollectionAttemptRecord(
        job_id="sebi-rss:1", source_id="sebi-rss", scheduled_for=NOW,
        started_at=NOW, completed_at=NOW + timedelta(seconds=15), attempt_ordinal=2,
        transport_status="SUCCEEDED", error_class="ConnectTimeout", handler_status="RECOVERED",
        parse_status="PASS", records_seen=30, canonical_events=0, duplicate_count=30,
        recovered=True, terminal_job_status="SUCCEEDED", latency_ms=15000,
        provenance_hash="collection-provenance",
    )
    store.add_collection_attempt(row)
    saved = store.connection.execute("SELECT payload_json FROM collection_attempts").fetchone()
    assert "ConnectTimeout" in saved[0] and '"recovered":true' in saved[0]
    store.close()
