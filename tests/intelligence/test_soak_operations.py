from datetime import UTC, date, datetime, timedelta

from intelligence_core.soak_operations import (
    AlertThresholds,
    EntityResolutionOutcome,
    SoakManifest,
    SoakTelemetryStore,
    aggregate_costs,
    budget_state,
    full_content_access_state,
    incident_types,
    make_cost_entry,
    runtime_metrics,
)


def entry(*, cost_input=1000, cost_output=100, cache=False, error=None, schema=True):
    return make_cost_entry(
        occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
        provider="openai",
        model="gpt-5.6-luna",
        task="EVENT_CLASSIFICATION",
        source_id="rbi",
        canonical_event_id="event-1",
        input_tokens=cost_input,
        output_tokens=cost_output,
        cache_hit=cache,
        latency_ms=100,
        input_price_per_million=0 if cache else 0.20,
        output_price_per_million=0 if cache else 1.20,
        error_class=error,
        schema_valid=schema,
    )


def test_cost_ledger_reconciles_components_and_dimensions():
    result = aggregate_costs([entry()])
    assert result["input_cost_usd"] == 0.0002
    assert result["output_cost_usd"] == 0.00012
    assert result["total_cost_usd"] == 0.00032
    assert result["by_provider"] == {"openai": 0.00032}
    assert result["by_task"] == {"EVENT_CLASSIFICATION": 0.00032}
    assert result["by_source"] == {"rbi": 0.00032}


def test_daily_aggregation_excludes_other_dates():
    other = entry().model_copy(update={"occurred_at": datetime(2026, 9, 1, tzinfo=UTC)})
    assert aggregate_costs([entry(), other], report_date=date(2026, 8, 31))["entries"] == 1


def test_application_cache_has_zero_cost_and_tracks_savings():
    cached = entry(cache=True)
    result = aggregate_costs([cached])
    assert result["total_cost_usd"] == 0
    assert result["cache_savings_usd"] == 0.00032
    assert runtime_metrics([cached])["cache_hit_rate"] == 1


def test_budget_warning_and_exhaustion():
    assert budget_state(spent_usd=0.19, ceiling_usd=0.25, warning_fraction=0.8) == "HEALTHY"
    assert budget_state(spent_usd=0.20, ceiling_usd=0.25, warning_fraction=0.8) == "WARNING"
    assert budget_state(spent_usd=0.25, ceiling_usd=0.25, warning_fraction=0.8) == "EXCEEDED"


def test_incident_thresholds_are_operational():
    thresholds = AlertThresholds(
        version="v1",
        schema_failure_rate=0.05,
        consecutive_provider_errors=2,
        budget_warning_fraction=0.8,
        source_stale_seconds=2700,
    )
    failures = [entry(error="OPENAI_RATE_LIMIT_429", schema=False), entry(error="HTTP", schema=False)]
    types = incident_types(entries=failures, spent_usd=0.21, budget_usd=0.25, thresholds=thresholds)
    assert set(types) == {
        "LLM_COST_BUDGET_WARNING",
        "LLM_PROVIDER_DOWN",
        "LLM_SCHEMA_FAILURE_SPIKE",
        "LLM_RATE_LIMITED",
    }


def test_soak_manifest_detects_prompt_model_schema_or_route_change():
    now = datetime(2026, 8, 31, tzinfo=UTC)
    manifest = SoakManifest(
        version="v1",
        started_at=now,
        target_end_at=now + timedelta(hours=24),
        model="gpt-5.6-luna",
        prompt_version="p1",
        schema_hash="s1",
        routing_hash="r1",
        config_hash="c1",
        code_sha="abc",
    )
    manifest.assert_frozen(manifest.model_copy())
    try:
        manifest.assert_frozen(manifest.model_copy(update={"prompt_version": "p2"}))
    except ValueError as error:
        assert "CHANGED" in str(error)
    else:
        raise AssertionError("changed prompt was accepted")
    try:
        manifest.assert_frozen(manifest.model_copy(update={"source_registry_hash": "changed"}))
    except ValueError as error:
        assert "CHANGED" in str(error)
    else:
        raise AssertionError("changed source registry was accepted")


def test_entity_resolution_outcome_categories_are_stable():
    assert {value.value for value in EntityResolutionOutcome} == {
        "CORRECTLY_NON_COMPANY_SPECIFIC",
        "EXPLICIT_ENTITY_NOT_RESOLVED",
        "INSUFFICIENT_METADATA",
        "RESOLUTION_BUG",
        "SOURCE_DOES_NOT_SUPPORT_ENTITY",
    }


def test_telemetry_store_persists_cost_and_cache(tmp_path):
    store = SoakTelemetryStore(tmp_path / "soak.sqlite3")
    store.add_cost(entry())
    store.cache_put("k", {"value": 1}, datetime.now(UTC))
    assert len(store.costs()) == 1
    assert store.cache_get("k") == {"value": 1}
    store.close()


def test_full_document_access_remains_metadata_only_when_rights_are_separate():
    assert full_content_access_state(
        retention_status="RSS_METADATA_AND_HASH",
        notes="Official RSS; document content rights remain separate.",
    ) == "TITLE_METADATA_ONLY"
