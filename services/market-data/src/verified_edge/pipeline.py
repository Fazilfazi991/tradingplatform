from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from verified_edge.domain import (
    DailyBar,
    Instrument,
    QualityEvent,
    QualityStatus,
    RawObservation,
    Severity,
)
from verified_edge.quality import validate_observations


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def make_raw_observations(
    provider: str,
    instrument: Instrument,
    rows: Iterable[dict[str, Any]],
    run_id: UUID | None = None,
    observed_at: datetime | None = None,
) -> list[RawObservation]:
    run_id = run_id or uuid4()
    observed_at = observed_at or datetime.now(UTC)
    result = []
    for row in rows:
        timestamp = row["timestamp"]
        if timestamp.tzinfo is None:
            raise ValueError("provider timestamp must be timezone-aware")
        payload = {key: row.get(key) for key in ("open", "high", "low", "close", "volume", "oi")}
        result.append(
            RawObservation(
                provider=provider,
                instrument_id=instrument.id,
                session_date=timestamp.date(),
                observed_at=observed_at,
                source_timestamp=timestamp,
                raw_payload=payload,
                payload_hash=stable_hash(payload),
                ingestion_run_id=run_id,
            )
        )
    return result


def canonicalize(
    observations: Iterable[RawObservation],
    instruments: dict[UUID, Instrument],
    expected_sessions: set[date] | None = None,
    canonical_version: int = 1,
) -> tuple[list[DailyBar], list[QualityEvent], list[RawObservation]]:
    rows = list(observations)
    events = validate_observations(rows, expected_sessions)
    critical_keys = {
        (e.instrument_id, e.session_date) for e in events if e.severity == Severity.CRITICAL
    }
    duplicate_keys = {
        (e.instrument_id, e.session_date)
        for e in events
        if e.check_code in {"DUPLICATE_BAR", "CONFLICTING_RETRY"}
    }
    bars: list[DailyBar] = []
    quarantined: list[RawObservation] = []
    seen: set[tuple] = set()
    warning_keys = {
        (e.instrument_id, e.session_date) for e in events if e.severity == Severity.WARNING
    }
    for row in rows:
        key = (row.instrument_id, row.session_date)
        if key in critical_keys or key in duplicate_keys:
            quarantined.append(row)
            continue
        if key in seen:
            continue
        seen.add(key)
        payload = row.raw_payload
        instrument = instruments[row.instrument_id]
        transform = {
            "canonical_version": canonical_version,
            "raw_hash": row.payload_hash,
            "mapping": "decimal OHLC, integer volume/OI, no adjustment",
        }
        bars.append(
            DailyBar(
                instrument_id=row.instrument_id,
                symbol=instrument.symbol,
                session_date=row.session_date,
                open=Decimal(str(payload["open"])),
                high=Decimal(str(payload["high"])),
                low=Decimal(str(payload["low"])),
                close=Decimal(str(payload["close"])),
                volume=int(payload["volume"]),
                oi=int(payload["oi"]) if payload.get("oi") is not None else None,
                provider=row.provider,
                raw_observation_id=row.id,
                canonical_version=canonical_version,
                transformation_hash=stable_hash(transform),
                quality_status=QualityStatus.WARNING
                if key in warning_keys
                else QualityStatus.ACCEPTED,
            )
        )
    return sorted(bars, key=lambda bar: (bar.symbol, bar.session_date)), events, quarantined
