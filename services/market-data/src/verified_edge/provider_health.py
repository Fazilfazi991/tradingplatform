from __future__ import annotations

import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from verified_edge.pipeline import stable_hash
from verified_edge.providers.upstox import (
    AuthenticationError,
    ProviderError,
    ProviderSchemaError,
    RateLimitError,
)


class HealthProvider(Protocol):
    def get_market_status(self, exchange: str = "NSE") -> dict[str, Any]: ...


class MarketProviderHealthRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str = Field(default_factory=lambda: str(uuid4()))
    provider: Literal["UPSTOX"] = "UPSTOX"
    exchange: Literal["NSE"] = "NSE"
    checked_at: datetime
    status: Literal[
        "HEALTHY", "AUTHENTICATION_FAILED", "RATE_LIMITED", "SCHEMA_FAILED", "UNAVAILABLE"
    ]
    market_status: str | None = None
    latency_ms: float = Field(ge=0)
    credential_name: Literal["UPSTOX_ANALYTICS_TOKEN"] = "UPSTOX_ANALYTICS_TOKEN"
    credential_value_recorded: Literal[False] = False
    error_class: str | None = None
    public_delivery: Literal["BLOCKED"] = "BLOCKED"
    record_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> MarketProviderHealthRecord:
        if self.status == "HEALTHY" and (not self.market_status or self.error_class):
            raise ValueError("healthy provider record requires status and no error")
        if self.status != "HEALTHY" and not self.error_class:
            raise ValueError("failed provider record requires sanitized error class")
        expected = stable_hash(self.model_dump(exclude={"record_hash"}, mode="json"))
        if self.record_hash and self.record_hash != expected:
            raise ValueError("provider health record hash mismatch")
        if not self.record_hash:
            object.__setattr__(self, "record_hash", expected)
        return self


class MarketProviderHealthLedger:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(Path(path))
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS market_provider_health (
          record_id TEXT PRIMARY KEY, checked_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS market_provider_health_no_update
          BEFORE UPDATE ON market_provider_health BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS market_provider_health_no_delete
          BEFORE DELETE ON market_provider_health BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        """)
        self.connection.commit()

    def append(self, record: MarketProviderHealthRecord) -> None:
        self.connection.execute(
            "INSERT INTO market_provider_health VALUES(?,?,?)",
            (record.record_id, record.checked_at.astimezone(UTC).isoformat(), record.model_dump_json()),
        )
        self.connection.commit()

    def records(self) -> list[MarketProviderHealthRecord]:
        return [
            MarketProviderHealthRecord.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM market_provider_health ORDER BY checked_at,record_id"
            )
        ]

    def report(self, *, now: datetime, stale_after: timedelta = timedelta(minutes=30)) -> dict[str, Any]:
        records = self.records()
        latest = records[-1] if records else None
        stale = latest is None or now.astimezone(UTC) - latest.checked_at.astimezone(UTC) > stale_after
        return {
            "provider": "UPSTOX",
            "status": "NOT_CHECKED" if latest is None else "STALE" if stale else latest.status,
            "latest_checked_at": latest.checked_at.isoformat() if latest else None,
            "market_status": latest.market_status if latest else None,
            "latency_ms": latest.latency_ms if latest else None,
            "checks": len(records),
            "stale_after_seconds": int(stale_after.total_seconds()),
            "credential_value_recorded": False,
            "public_delivery": "BLOCKED",
            "ledger_hash": stable_hash([record.record_hash for record in records]),
        }

    def close(self) -> None:
        self.connection.close()


def check_market_provider(provider: HealthProvider, *, now: datetime) -> MarketProviderHealthRecord:
    started = time.perf_counter()
    try:
        result = provider.get_market_status("NSE")
        if result.get("exchange") != "NSE" or not result.get("status"):
            raise ProviderSchemaError("malformed market status")
        return MarketProviderHealthRecord(
            checked_at=now,
            status="HEALTHY",
            market_status=str(result["status"]),
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except AuthenticationError:
        state, error = "AUTHENTICATION_FAILED", "AuthenticationError"
    except RateLimitError:
        state, error = "RATE_LIMITED", "RateLimitError"
    except ProviderSchemaError:
        state, error = "SCHEMA_FAILED", "ProviderSchemaError"
    except ProviderError:
        state, error = "UNAVAILABLE", "ProviderError"
    return MarketProviderHealthRecord(
        checked_at=now,
        status=state,
        latency_ms=round((time.perf_counter() - started) * 1000, 2),
        error_class=error,
    )
