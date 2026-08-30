from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from itertools import pairwise

from verified_edge.domain import QualityEvent, RawObservation, Severity


def validate_observations(
    observations: Iterable[RawObservation],
    expected_sessions: set[date] | None = None,
    extreme_return_threshold: Decimal = Decimal("0.30"),
) -> list[QualityEvent]:
    rows = list(observations)
    events: list[QualityEvent] = []
    by_key: dict[tuple, list[RawObservation]] = defaultdict(list)
    by_instrument: dict[object, list[RawObservation]] = defaultdict(list)
    now = datetime.now(UTC)
    for row in rows:
        by_key[(row.instrument_id, row.session_date)].append(row)
        by_instrument[row.instrument_id].append(row)
        payload = row.raw_payload
        required = {"open", "high", "low", "close", "volume"}
        missing = required - payload.keys()
        if missing:
            events.append(
                _event(
                    Severity.CRITICAL,
                    "MISSING_REQUIRED_FIELDS",
                    row,
                    sorted(missing),
                    sorted(required),
                    "required candle fields missing",
                )
            )
            continue
        try:
            o, h, l, c = (Decimal(str(payload[name])) for name in ("open", "high", "low", "close"))
            volume = Decimal(str(payload["volume"]))
            oi = Decimal(str(payload["oi"])) if payload.get("oi") is not None else Decimal(0)
        except (InvalidOperation, TypeError, ValueError):
            events.append(
                _event(
                    Severity.CRITICAL,
                    "MALFORMED_NUMERIC",
                    row,
                    payload,
                    "numeric OHLCV",
                    "provider returned malformed numeric data",
                )
            )
            continue
        if min(o, h, l, c, volume, oi) < 0:
            events.append(
                _event(
                    Severity.CRITICAL,
                    "NEGATIVE_VALUE",
                    row,
                    payload,
                    ">= 0",
                    "negative price, volume or OI",
                )
            )
        if not (h >= o and h >= c and l <= o and l <= c and h >= l):
            events.append(
                _event(
                    Severity.CRITICAL,
                    "INVALID_OHLC",
                    row,
                    {"o": o, "h": h, "l": l, "c": c},
                    "high >= open/close >= low",
                    "OHLC relationship failed",
                )
            )
        if volume == 0:
            events.append(
                _event(
                    Severity.WARNING,
                    "ZERO_VOLUME",
                    row,
                    0,
                    "> 0 or legitimate exception",
                    "zero volume requires review",
                )
            )
        if row.source_timestamp > now or row.observed_at > now:
            events.append(
                _event(
                    Severity.CRITICAL,
                    "FUTURE_TIMESTAMP",
                    row,
                    row.source_timestamp,
                    f"<= {now.isoformat()}",
                    "future information is ineligible",
                )
            )
        if row.source_timestamp.date() != row.session_date:
            events.append(
                _event(
                    Severity.ERROR,
                    "SESSION_TIMESTAMP_MISMATCH",
                    row,
                    row.source_timestamp.date(),
                    row.session_date,
                    "source timestamp does not align to session",
                )
            )
        if expected_sessions is not None and row.session_date not in expected_sessions:
            events.append(
                _event(
                    Severity.ERROR,
                    "NON_TRADING_SESSION",
                    row,
                    row.session_date,
                    "exchange session",
                    "bar date is outside calendar",
                )
            )
    for key, duplicates in by_key.items():
        hashes = {row.payload_hash for row in duplicates}
        if len(duplicates) > 1:
            severity = Severity.CRITICAL if len(hashes) > 1 else Severity.WARNING
            code = "CONFLICTING_RETRY" if len(hashes) > 1 else "DUPLICATE_BAR"
            events.append(
                QualityEvent(
                    severity=severity,
                    check_code=code,
                    instrument_id=key[0],
                    session_date=key[1],
                    observed=list(hashes),
                    expected="one stable payload",
                    reason="duplicate session observations",
                )
            )
    for instrument_id, instrument_rows in by_instrument.items():
        ordered = sorted(instrument_rows, key=lambda row: row.session_date)
        if expected_sessions:
            present = {row.session_date for row in ordered}
            for missing_date in sorted(expected_sessions - present):
                events.append(
                    QualityEvent(
                        severity=Severity.ERROR,
                        check_code="MISSING_SESSION",
                        instrument_id=instrument_id,
                        session_date=missing_date,
                        observed=None,
                        expected="daily bar",
                        reason="expected trading session absent",
                    )
                )
        for previous, current in pairwise(ordered):
            try:
                prior = Decimal(str(previous.raw_payload["close"]))
                close = Decimal(str(current.raw_payload["close"]))
                change = abs(close / prior - 1) if prior else Decimal(0)
                if change > extreme_return_threshold:
                    events.append(
                        _event(
                            Severity.WARNING,
                            "EXTREME_RETURN",
                            current,
                            change,
                            f"<= {extreme_return_threshold}",
                            "extreme move; corporate action may explain it",
                        )
                    )
            except (KeyError, InvalidOperation, TypeError):
                pass
    return events


def _event(
    severity: Severity,
    code: str,
    row: RawObservation,
    observed: object,
    expected: object,
    reason: str,
) -> QualityEvent:
    return QualityEvent(
        severity=severity,
        check_code=code,
        instrument_id=row.instrument_id,
        session_date=row.session_date,
        observed=observed,
        expected=expected,
        reason=reason,
    )
