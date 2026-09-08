import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from verified_edge.provider_health import (
    MarketProviderHealthLedger,
    check_market_provider,
)
from verified_edge.providers.upstox import AuthenticationError, RateLimitError

NOW = datetime(2026, 9, 8, 12, tzinfo=UTC)


class Provider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def get_market_status(self, exchange: str = "NSE"):
        if self.error:
            raise self.error
        return {"exchange": exchange, "status": "CLOSING_END"}


def test_health_ledger_is_sanitized_append_only_and_fresh(tmp_path):
    ledger = MarketProviderHealthLedger(tmp_path / "health.sqlite3")
    record = check_market_provider(Provider(), now=NOW)
    ledger.append(record)
    report = ledger.report(now=NOW + timedelta(minutes=1))
    assert report["status"] == "HEALTHY"
    assert report["market_status"] == "CLOSING_END"
    assert report["credential_value_recorded"] is False
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        ledger.connection.execute("DELETE FROM market_provider_health")
    assert ledger.report(now=NOW + timedelta(hours=1))["status"] == "STALE"
    ledger.close()


@pytest.mark.parametrize(
    ("error", "status", "error_class"),
    [
        (AuthenticationError("secret response"), "AUTHENTICATION_FAILED", "AuthenticationError"),
        (RateLimitError("secret response"), "RATE_LIMITED", "RateLimitError"),
    ],
)
def test_failure_records_only_sanitized_error_class(error, status, error_class):
    record = check_market_provider(Provider(error), now=NOW)
    assert record.status == status
    assert record.error_class == error_class
    assert "secret response" not in record.model_dump_json()
