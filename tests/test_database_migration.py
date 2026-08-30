from pathlib import Path

SQL = (
    Path("infra/migrations/0001_prediction_data_foundation.sql").read_text(encoding="utf-8").lower()
)


def test_private_schema_and_public_access_revoked():
    assert "create schema if not exists verified_edge" in SQL
    assert "revoke all on all tables in schema verified_edge from public" in SQL
    assert "where rolname = 'anon'" in SQL and "where rolname = 'authenticated'" in SQL


def test_append_only_triggers_present():
    for table in ("market_observations_raw", "daily_bars_canonical", "information_events"):
        assert f"on verified_edge.{table}" in SQL
    assert "sealed dataset cannot mutate" in SQL


def test_database_constraints_present():
    assert "check(high >= open and high >= close" in SQL
    assert (
        "unique(provider_id,instrument_id,observation_type,interval,session_date,payload_hash)"
        in SQL
    )
    assert "check(available_at >= published_at)" in SQL
