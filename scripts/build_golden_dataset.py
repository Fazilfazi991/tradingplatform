"""Build deterministic non-live QA artifacts from the hand-calculated golden fixture."""

import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid5

from verified_edge.dataset import build_manifest, export_parquet, seal_manifest
from verified_edge.domain import Instrument
from verified_edge.pipeline import canonicalize, make_raw_observations


def main() -> None:
    fixture = json.loads(Path("research/fixtures/golden_market_data.json").read_text(encoding="utf-8"))
    instruments = {
        symbol: Instrument(id=uuid5(UUID(int=0), symbol), exchange="NSE", segment="NSE_EQ",
            symbol=symbol, provider_instrument_key=f"NSE_EQ|{symbol}")
        for symbol in ("ALPHA", "BETA")
    }
    raw = []
    for symbol, day, open_, high, low, close, volume in fixture["rows"]:
        raw += make_raw_observations("GOLDEN", instruments[symbol], [{
            "timestamp": datetime.fromisoformat(f"{day}T00:00:00+05:30"), "open": open_,
            "high": high, "low": low, "close": close, "volume": volume, "oi": None,
        }], observed_at=datetime.fromisoformat("2026-02-01T00:00:00+00:00"))
    sessions = {date.fromisoformat(value) for value in fixture["expected_sessions"]}
    bars, events, quarantine = canonicalize(raw, {i.id: i for i in instruments.values()}, sessions)
    target, file_hash, row_count = export_parquet(bars, "data/exports/golden_batch1.parquet")
    code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    manifest = build_manifest(purpose="Batch 1 golden fixture verification",
        universe={"code": "GOLDEN_FIXTURE", "version": "1", "point_in_time": True}, bars=bars,
        file_references=[{"path": target.as_posix(), "sha256": file_hash}], code_sha=code_sha,
        trading_calendar_version="GOLDEN_1", corporate_action_version="UNRESOLVED_FIXTURE",
        adjustment_version="RAW_UNADJUSTED", quality_rules_version="1",
        created_at=datetime.fromisoformat("2026-08-30T00:00:00+00:00"))
    sealed = seal_manifest(manifest, datetime.fromisoformat("2026-08-30T00:00:01+00:00"))
    output = Path("data/manifests/golden_batch1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sealed, sort_keys=True, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"artifact": target.as_posix(), "rows": row_count,
        "symbols": len({bar.symbol for bar in bars}), "date_start": min(bar.session_date for bar in bars),
        "date_end": max(bar.session_date for bar in bars), "quality_events": len(events),
        "quarantined": len(quarantine), "parquet_sha256": file_hash,
        "dataset_sha256": sealed["sha256"], "manifest": output.as_posix()}, default=str))


if __name__ == "__main__":
    main()
