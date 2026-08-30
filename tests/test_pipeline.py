from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from verified_edge.domain import Instrument, QualityStatus, RawObservation
from verified_edge.pipeline import canonicalize, make_raw_observations, stable_hash


def instrument(symbol="ALPHA"):
    return Instrument(
        exchange="NSE", segment="NSE_EQ", symbol=symbol, provider_instrument_key=f"NSE_EQ|{symbol}"
    )


def raw(inst, day, o=100, h=110, l=90, c=105, v=1000, payload_hash=None):
    payload = {"open": o, "high": h, "low": l, "close": c, "volume": v, "oi": None}
    stamp = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
    return RawObservation(
        provider="FIXTURE",
        instrument_id=inst.id,
        session_date=day,
        observed_at=stamp,
        source_timestamp=stamp,
        raw_payload=payload,
        payload_hash=payload_hash or stable_hash(payload),
        ingestion_run_id=uuid4(),
    )


def test_instrument_mapping_and_raw_creation():
    inst = instrument()
    rows = [
        {
            "timestamp": datetime(2026, 1, 2, tzinfo=UTC),
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
            "volume": 10,
            "oi": None,
        }
    ]
    made = make_raw_observations("UPSTOX", inst, rows)
    assert made[0].instrument_id == inst.id
    assert made[0].payload_hash == stable_hash(made[0].raw_payload)


def test_normal_observation_canonicalizes():
    inst = instrument()
    bars, events, quarantine = canonicalize([raw(inst, date(2026, 1, 2))], {inst.id: inst})
    assert len(bars) == 1 and not quarantine
    assert bars[0].close == Decimal(105)
    assert not [event for event in events if event.severity.value == "CRITICAL"]


def test_invalid_ohlc_quarantines():
    inst = instrument()
    bars, events, quarantine = canonicalize(
        [raw(inst, date(2026, 1, 2), h=101, c=105)], {inst.id: inst}
    )
    assert not bars and len(quarantine) == 1
    assert any(e.check_code == "INVALID_OHLC" for e in events)


def test_identical_duplicate_is_quarantined_not_duplicated():
    inst = instrument()
    row = raw(inst, date(2026, 1, 2))
    duplicate = row.model_copy(update={"id": uuid4()})
    bars, events, quarantine = canonicalize([row, duplicate], {inst.id: inst})
    assert not bars and len(quarantine) == 2
    assert any(e.check_code == "DUPLICATE_BAR" for e in events)


def test_conflicting_retry_is_critical():
    inst = instrument()
    rows = [raw(inst, date(2026, 1, 2)), raw(inst, date(2026, 1, 2), c=104)]
    bars, events, quarantine = canonicalize(rows, {inst.id: inst})
    assert not bars and len(quarantine) == 2
    assert any(
        e.check_code == "CONFLICTING_RETRY" and e.severity.value == "CRITICAL" for e in events
    )


def test_extreme_move_is_warning_not_silently_fixed():
    inst = instrument()
    rows = [
        raw(inst, date(2026, 1, 2), c=100),
        raw(inst, date(2026, 1, 5), o=150, h=160, l=145, c=150),
    ]
    bars, events, quarantine = canonicalize(rows, {inst.id: inst})
    assert len(bars) == 2 and not quarantine
    assert bars[1].quality_status == QualityStatus.WARNING
    assert any(e.check_code == "EXTREME_RETURN" for e in events)


def test_missing_session_event():
    inst = instrument()
    expected = {date(2026, 1, 2), date(2026, 1, 5)}
    _, events, _ = canonicalize([raw(inst, date(2026, 1, 2))], {inst.id: inst}, expected)
    assert any(
        e.check_code == "MISSING_SESSION" and e.session_date == date(2026, 1, 5) for e in events
    )
