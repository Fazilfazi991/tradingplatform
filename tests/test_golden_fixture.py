import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid5

from verified_edge.domain import Instrument
from verified_edge.pipeline import canonicalize, make_raw_observations


def test_hand_calculated_golden_fixture():
    fixture = json.loads(
        Path("research/fixtures/golden_market_data.json").read_text(encoding="utf-8")
    )
    instruments = {
        symbol: Instrument(
            id=uuid5(UUID(int=0), symbol),
            exchange="NSE",
            segment="NSE_EQ",
            symbol=symbol,
            provider_instrument_key=f"NSE_EQ|{symbol}",
        )
        for symbol in ("ALPHA", "BETA")
    }
    raw = []
    for symbol, day, open_, high, low, close, volume in fixture["rows"]:
        stamp = datetime.fromisoformat(f"{day}T00:00:00+05:30")
        raw.extend(
            make_raw_observations(
                "GOLDEN",
                instruments[symbol],
                [
                    {
                        "timestamp": stamp,
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                        "oi": None,
                    }
                ],
                observed_at=datetime.fromisoformat("2026-02-01T00:00:00+00:00"),
            )
        )
    expected_sessions = {date.fromisoformat(value) for value in fixture["expected_sessions"]}
    bars, events, quarantine = canonicalize(
        raw, {item.id: item for item in instruments.values()}, expected_sessions
    )
    counts = {
        code: sum(event.check_code == code for event in events)
        for code in ("MISSING_SESSION", "DUPLICATE_BAR", "INVALID_OHLC", "EXTREME_RETURN")
    }
    assert counts == {
        "MISSING_SESSION": 1,
        "DUPLICATE_BAR": 1,
        "INVALID_OHLC": 1,
        "EXTREME_RETURN": 2,
    }
    assert len(quarantine) == fixture["expected"]["quarantined_rows"]
    assert len(bars) == fixture["expected"]["canonical_rows"]
