from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from verified_edge.domain import DailyBar, Instrument
from verified_edge.pipeline import stable_hash
from verified_edge.real_market import canonicalize_provider_rows, map_current_universe

IST = ZoneInfo("Asia/Kolkata")


class EodError(ValueError):
    pass


class EodProvider(Protocol):
    def get_market_status(self, exchange: str = "NSE") -> dict[str, Any]: ...

    def get_instruments(self) -> list[Instrument]: ...

    def get_historical_daily(
        self, instrument: Instrument, start: date, end: date
    ) -> list[dict[str, Any]]: ...


class EodConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: str
    timezone: str
    provider: str
    credential: str
    schedule: dict[str, Any]
    session_gate: dict[str, Any]
    pipeline: list[str]
    collection_mode: str
    public_output: bool
    execution_operations: bool

    @model_validator(mode="after")
    def validate_boundary(self) -> EodConfig:
        if self.provider != "UPSTOX" or self.credential != "UPSTOX_ANALYTICS_TOKEN":
            raise ValueError("EOD runtime requires the read-only Upstox analytics credential")
        if self.public_output or self.collection_mode != "FORWARD_COLLECTED_MARKET_DATA":
            raise ValueError("EOD runtime must remain internal forward collection")
        if self.timezone != "Asia/Kolkata" or self.schedule.get("kind") != "DAILY":
            raise ValueError("unsupported EOD schedule")
        return self


class EodBarRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: str
    run_id: str
    symbol: str
    session_date: date
    observed_at: datetime
    bar: dict[str, Any]
    source_payload_hash: str = Field(min_length=64, max_length=64)
    canonical_hash: str = Field(min_length=64, max_length=64)
    public_delivery: Literal["BLOCKED"] = "BLOCKED"


class EodRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    session_date: date
    started_at: datetime
    completed_at: datetime
    config_version: str
    provider: str
    market_status: str
    expected_symbols: int
    accepted_symbols: tuple[str, ...]
    missing_symbols: tuple[str, ...]
    quarantined_symbols: tuple[str, ...]
    state: str
    public_delivery: Literal["BLOCKED"] = "BLOCKED"
    record_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> EodRun:
        expected = stable_hash(self.model_dump(exclude={"record_hash"}, mode="json"))
        if self.record_hash and self.record_hash != expected:
            raise ValueError("EOD run hash mismatch")
        if not self.record_hash:
            object.__setattr__(self, "record_hash", expected)
        return self


class EodLedger:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(Path(path))
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS eod_runs (
          run_id TEXT PRIMARY KEY, uniqueness_key TEXT UNIQUE NOT NULL,
          completed_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS eod_bars (
          event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, symbol TEXT NOT NULL,
          session_date TEXT NOT NULL, payload_json TEXT NOT NULL,
          FOREIGN KEY(run_id) REFERENCES eod_runs(run_id)
        );
        CREATE TRIGGER IF NOT EXISTS eod_runs_no_update BEFORE UPDATE ON eod_runs
          BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS eod_runs_no_delete BEFORE DELETE ON eod_runs
          BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS eod_bars_no_update BEFORE UPDATE ON eod_bars
          BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS eod_bars_no_delete BEFORE DELETE ON eod_bars
          BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        """)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.commit()

    def append(self, run: EodRun, bars: list[EodBarRecord]) -> None:
        if any(bar.run_id != run.run_id for bar in bars):
            raise EodError("bar run identity mismatch")
        key = stable_hash(
            {
                "session_date": run.session_date,
                "provider": run.provider,
                "config_version": run.config_version,
            }
        )
        try:
            self.connection.execute(
                "INSERT INTO eod_runs VALUES(?,?,?,?)",
                (run.run_id, key, run.completed_at.isoformat(), run.model_dump_json()),
            )
            self.connection.executemany(
                "INSERT INTO eod_bars VALUES(?,?,?,?,?)",
                [
                    (
                        bar.event_id,
                        bar.run_id,
                        bar.symbol,
                        bar.session_date.isoformat(),
                        bar.model_dump_json(),
                    )
                    for bar in bars
                ],
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise EodError("duplicate or inconsistent EOD run") from error

    def report(self) -> dict[str, Any]:
        runs = [
            EodRun.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM eod_runs ORDER BY completed_at,run_id"
            )
        ]
        bars = int(self.connection.execute("SELECT COUNT(*) FROM eod_bars").fetchone()[0])
        latest = runs[-1] if runs else None
        return {
            "status": "ACTIVE_INTERNAL" if latest else "NOT_STARTED",
            "public_delivery": "BLOCKED",
            "runs": len(runs),
            "bars": bars,
            "latest_session": latest.session_date.isoformat() if latest else None,
            "latest_state": latest.state if latest else None,
            "ledger_hash": stable_hash([item.record_hash for item in runs]),
        }

    def close(self) -> None:
        self.connection.close()


class EodCollector:
    def __init__(
        self,
        provider: EodProvider,
        config: EodConfig,
        expected_universe: dict[str, dict[str, Any]],
    ) -> None:
        self.provider = provider
        self.config = config
        self.expected_universe = expected_universe

    def collect(self, session_date: date, *, now: datetime) -> tuple[EodRun, list[EodBarRecord]]:
        if not self.config.execution_operations:
            raise EodError("EOD execution operations are disabled")
        local = now.astimezone(IST)
        scheduled = time.fromisoformat(str(self.config.schedule["local_time"]))
        if local.date() != session_date or local.time().replace(tzinfo=None) < scheduled:
            raise EodError("EOD collection is outside the eligible local session window")
        if self.config.schedule.get("weekdays_only") and session_date.weekday() >= 5:
            raise EodError("ordinary weekend EOD collection is disabled")
        market = self.provider.get_market_status(str(self.config.session_gate["exchange"]))
        if market.get("status") not in self.config.session_gate["required_status"]:
            raise EodError("exchange session is not complete")
        mappings = map_current_universe(
            self.expected_universe, self.provider.get_instruments()
        )
        if any(item.instrument is None for item in mappings):
            raise EodError("current universe mapping is incomplete or ambiguous")
        run_id = str(uuid4())
        accepted: list[str] = []
        missing: list[str] = []
        quarantined: list[str] = []
        records: list[EodBarRecord] = []
        for mapping in mappings:
            assert mapping.instrument is not None
            expected = self.expected_universe[mapping.symbol]
            instrument = mapping.instrument.model_copy(
                update={"id": UUID(expected["internal_instrument_id"])}
            )
            observed_at = datetime.now(UTC)
            rows = self.provider.get_historical_daily(instrument, session_date, session_date)
            matching = [
                row for row in rows if row["timestamp"].astimezone(IST).date() == session_date
            ]
            if not matching:
                missing.append(mapping.symbol)
                continue
            bars, _events, invalid = canonicalize_provider_rows(
                instrument, matching, observed_at
            )
            exact = [bar for bar in bars if bar.session_date == session_date]
            if invalid or len(exact) != 1:
                quarantined.append(mapping.symbol)
                continue
            bar: DailyBar = exact[0]
            payload_hash = stable_hash(matching[0]["provider_row"])
            canonical = bar.model_dump(mode="json")
            canonical_hash = stable_hash(canonical)
            records.append(
                EodBarRecord(
                    event_id=stable_hash(
                        {
                            "run_id": run_id,
                            "symbol": mapping.symbol,
                            "session_date": session_date,
                            "canonical_hash": canonical_hash,
                        }
                    ),
                    run_id=run_id,
                    symbol=mapping.symbol,
                    session_date=session_date,
                    observed_at=observed_at,
                    bar=canonical,
                    source_payload_hash=payload_hash,
                    canonical_hash=canonical_hash,
                )
            )
            accepted.append(mapping.symbol)
        state = "COMPLETE" if len(accepted) == len(mappings) else "DEGRADED_QUARANTINED"
        completed = datetime.now(UTC)
        return (
            EodRun(
                run_id=run_id,
                session_date=session_date,
                started_at=now,
                completed_at=completed,
                config_version=self.config.version,
                provider=self.config.provider,
                market_status=str(market["status"]),
                expected_symbols=len(mappings),
                accepted_symbols=tuple(accepted),
                missing_symbols=tuple(missing),
                quarantined_symbols=tuple(quarantined),
                state=state,
            ),
            records,
        )
