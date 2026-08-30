import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid5

from verified_edge.dataset import build_manifest, export_parquet
from verified_edge.domain import Instrument
from verified_edge.pipeline import canonicalize, make_raw_observations


def build_fixture():
    fixture = json.loads(Path("research/fixtures/golden_market_data.json").read_text())
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
    run_id = uuid5(UUID(int=0), "batch-1.1-replay")
    observed_at = datetime(2026, 2, 1, tzinfo=UTC)
    for symbol, day, open_, high, low, close, volume in fixture["rows"]:
        raw += make_raw_observations(
            "GOLDEN",
            instruments[symbol],
            [{
                "timestamp": datetime.fromisoformat(f"{day}T00:00:00+05:30"),
                "open": open_, "high": high, "low": low, "close": close,
                "volume": volume, "oi": None,
            }],
            run_id=run_id,
            observed_at=observed_at,
        )
    sessions = {date.fromisoformat(value) for value in fixture["expected_sessions"]}
    return raw, {item.id: item for item in instruments.values()}, sessions


def test_raw_replay_and_derived_rebuild_are_identical(tmp_path):
    raw, instruments, sessions = build_fixture()
    first = canonicalize(raw, instruments, sessions)
    replay = canonicalize(raw, instruments, sessions)
    assert first[0] == replay[0]
    assert first[2] == replay[2]
    assert [event.model_dump(exclude={"id"}) for event in first[1]] == [
        event.model_dump(exclude={"id"}) for event in replay[1]
    ]

    hashes = []
    manifest_hashes = []
    for name in ("first.parquet", "rebuilt.parquet"):
        path, digest, count = export_parquet(first[0], tmp_path / name)
        hashes.append(digest)
        manifest = build_manifest(
            purpose="deterministic replay QA",
            universe={"code": "GOLDEN", "version": "1"},
            bars=first[0],
            file_references=[{"path": "dataset.parquet", "sha256": digest, "rows": count}],
            code_sha="2f605662cd315479a84036b577a49be78796846b",
            trading_calendar_version="fixture-v1",
            corporate_action_version="none-blocked",
            adjustment_version="unadjusted-v1",
            quality_rules_version="v1",
            created_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
        manifest_hashes.append(manifest["sha256"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert len(set(hashes)) == 1
    assert len(set(manifest_hashes)) == 1
