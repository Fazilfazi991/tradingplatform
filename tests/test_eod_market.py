import sqlite3
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from verified_edge.domain import Instrument
from verified_edge.eod import EodCollector, EodConfig, EodError, EodLedger

SESSION = date(2026, 9, 7)
NOW = datetime(2026, 9, 7, 11, tzinfo=UTC)  # 16:30 Asia/Kolkata


class Provider:
    def __init__(self) -> None:
        self.instruments = [
            Instrument(
                exchange="NSE",
                segment="NSE_EQ",
                symbol="AAA",
                isin="INE000A01001",
                provider_instrument_key="NSE_EQ|AAA",
            ),
            Instrument(
                exchange="NSE",
                segment="NSE_EQ",
                symbol="BBB",
                isin="INE000B01001",
                provider_instrument_key="NSE_EQ|BBB",
            ),
        ]

    def get_market_status(self, exchange="NSE"):
        return {"exchange": exchange, "status": "CLOSING_END"}

    def get_instruments(self):
        return self.instruments

    def get_historical_daily(self, instrument, start, end):
        assert start == end == SESSION
        row = ["2026-09-07T15:30:00+05:30", 100, 102, 99, 101, 1000, None]
        return [
            {
                "timestamp": datetime.fromisoformat(row[0]),
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "oi": row[6],
                "provider_row": row,
            }
        ]


def config(*, enabled=True):
    return EodConfig(
        version="1",
        timezone="Asia/Kolkata",
        provider="UPSTOX",
        credential="UPSTOX_ANALYTICS_TOKEN",
        schedule={"kind": "DAILY", "weekdays_only": True, "local_time": "16:15"},
        session_gate={"exchange": "NSE", "required_status": ["CLOSING_END"]},
        pipeline=["daily_bars", "quality"],
        collection_mode="FORWARD_COLLECTED_MARKET_DATA",
        public_output=False,
        execution_operations=enabled,
    )


def universe():
    return {
        "AAA": {"isin": "INE000A01001", "internal_instrument_id": str(uuid4())},
        "BBB": {"isin": "INE000B01001", "internal_instrument_id": str(uuid4())},
    }


def test_eod_collection_is_disabled_by_default_boundary():
    collector = EodCollector(Provider(), config(enabled=False), universe())
    with pytest.raises(EodError, match="disabled"):
        collector.collect(SESSION, now=NOW)


def test_eod_collects_one_exact_session_and_ledger_is_append_only(tmp_path):
    collector = EodCollector(Provider(), config(), universe())
    run, bars = collector.collect(SESSION, now=NOW)
    assert run.state == "COMPLETE"
    assert run.accepted_symbols == ("AAA", "BBB")
    assert len(bars) == 2
    assert all(bar.public_delivery == "BLOCKED" for bar in bars)
    ledger = EodLedger(tmp_path / "eod.sqlite3")
    ledger.append(run, bars)
    report = ledger.report()
    assert report["runs"] == 1 and report["bars"] == 2
    with pytest.raises(EodError, match="duplicate"):
        ledger.append(run.model_copy(update={"run_id": str(uuid4())}), [])
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        ledger.connection.execute("DELETE FROM eod_runs")
    ledger.close()


def test_eod_rejects_pre_close_and_incomplete_mapping():
    with pytest.raises(EodError, match="eligible local session"):
        EodCollector(Provider(), config(), universe()).collect(
            SESSION, now=datetime(2026, 9, 7, 9, tzinfo=UTC)
        )
    incomplete = universe()
    incomplete["MISSING"] = {
        "isin": "INE000M01001",
        "internal_instrument_id": str(uuid4()),
    }
    with pytest.raises(EodError, match="mapping is incomplete"):
        EodCollector(Provider(), config(), incomplete).collect(SESSION, now=NOW)
