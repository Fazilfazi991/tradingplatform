"""Activate read-only Upstox daily data in guarded A/B/C stages.

Runtime artifacts are written only below ignored ``data/local``. The script
never prints, persists, or returns the analytics credential.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
from research_core.analogues import find_analogues
from research_core.features import build_feature_matrix
from verified_edge.dataset import export_parquet
from verified_edge.pipeline import stable_hash
from verified_edge.providers.upstox import (
    AuthenticationError,
    ProviderError,
    UpstoxMarketDataProvider,
)
from verified_edge.real_market import (
    CollectionMode,
    DatasetState,
    canonicalize_provider_rows,
    daily_history_chunks,
    frame_for_research,
    map_current_universe,
    mapping_hash,
    real_market_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "data/manifests/current_nifty200_mapping.json"
RUNTIME = ROOT / "data/local/real-market-data"
STAGE_A = ("RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK")
STAGE_B = (
    "RELIANCE", "ONGC", "HDFCBANK", "ICICIBANK", "SBIN", "INFY", "TCS", "HCLTECH",
    "HINDUNILVR", "ITC", "MARUTI", "M&M", "SUNPHARMA", "CIPLA", "TATASTEEL",
    "HINDALCO", "LT", "SIEMENS", "TITAN", "TRENT", "BHARTIARTL", "ASIANPAINT",
    "ULTRACEMCO", "NTPC", "BAJFINANCE",
)


def load_secret() -> str:
    value = os.getenv("UPSTOX_ANALYTICS_TOKEN")
    if value:
        return value
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("UPSTOX_ANALYTICS_TOKEN="):
                value = line.split("=", 1)[1].strip().strip("\"'")
                break
    if not value:
        raise AuthenticationError("UPSTOX_ANALYTICS_TOKEN is absent; no live calls made")
    return value


def select_symbols(stage: str, all_symbols: list[str]) -> list[str]:
    if stage == "A":
        return [x for x in STAGE_A if x in all_symbols]
    if stage == "B":
        return [x for x in STAGE_B if x in all_symbols]
    if stage == "C":
        return all_symbols
    raise ValueError(f"unknown stage {stage}")


def main() -> int:
    stage = sys.argv[1].upper() if len(sys.argv) > 1 else "A"
    token = load_secret()
    provider = UpstoxMarketDataProvider(token=token)
    started = datetime.now(UTC)
    status = provider.get_market_status("NSE")
    universe = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    expected = universe["mappings"]
    mappings = map_current_universe(expected, provider.get_instruments())
    matched = {x.symbol: x.instrument for x in mappings if x.instrument is not None}
    if len(matched) != len(expected):
        summary = {"matched": len(matched), "ambiguous": sum(x.status == "AMBIGUOUS" for x in mappings),
                   "unmatched": sum(x.status == "UNMATCHED" for x in mappings)}
        print(json.dumps(summary, sort_keys=True))
        return 3
    # Preserve internal stable identities from the approved current snapshot.
    for symbol, instrument in list(matched.items()):
        assert instrument is not None
        matched[symbol] = instrument.model_copy(update={"id": UUID(expected[symbol]["internal_instrument_id"])})
    symbols = select_symbols(stage, sorted(matched))
    end = datetime.now(UTC).date() - timedelta(days=1)
    start = end.replace(year=end.year - 10) + timedelta(days=1)
    run_dir = RUNTIME / started.strftime("%Y%m%dT%H%M%SZ") / f"stage-{stage.lower()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    bars = []
    payload_hashes = []
    quality_events = []
    quarantined = []
    failures: dict[str, str] = {}
    corporate_actions: dict[str, Any] = {}
    request_ledger = []
    raw_records = []
    for symbol in symbols:
        instrument = matched[symbol]
        assert instrument is not None
        rows = []
        for chunk_start, chunk_end in daily_history_chunks(start, end):
            requested_at = datetime.now(UTC)
            try:
                chunk = provider.get_historical_daily(instrument, chunk_start, chunk_end)
            except ProviderError as exc:
                failures[symbol] = type(exc).__name__
                break
            received_at = datetime.now(UTC)
            chunk_hash = stable_hash([x["provider_row"] for x in chunk])
            payload_hashes.append(chunk_hash)
            request_ledger.append({
                "provider": "UPSTOX", "endpoint": "V3_HISTORICAL_CANDLE", "unit": "days",
                "interval": 1, "instrument_key": instrument.provider_instrument_key,
                "request_range": [chunk_start, chunk_end], "requested_at": requested_at,
                "received_at": received_at, "payload_hash": chunk_hash, "http_status": 200,
            })
            raw_records.extend({
                "symbol": symbol, "instrument_id": str(instrument.id),
                "instrument_key": instrument.provider_instrument_key,
                "timestamp": item["timestamp"], "open": item["open"], "high": item["high"],
                "low": item["low"], "close": item["close"], "volume": item["volume"],
                "oi": item["oi"], "provider_payload_hash": stable_hash(item["provider_row"]),
                "observed_at": received_at,
            } for item in chunk)
            rows.extend(chunk)
            time.sleep(0.03)
        if symbol in failures:
            continue
        canonical, events, bad = canonicalize_provider_rows(instrument, rows, datetime.now(UTC))
        bars.extend(canonical)
        quality_events.extend(events)
        quarantined.extend(bad)
        try:
            actions = provider.get_corporate_actions(instrument.isin or "")
            corporate_actions[symbol] = [x.model_dump(mode="json") for x in actions]
        except ProviderError as exc:
            corporate_actions[symbol] = {"status": "UNAVAILABLE", "error": type(exc).__name__}
        time.sleep(0.03)
    critical = sum(x.severity.value == "CRITICAL" for x in quality_events)
    # Invalid rows are excluded from canonical output. A bounded, fully recorded
    # quarantine does not contaminate the remaining dataset.
    state = DatasetState.RESEARCH_ELIGIBLE if not failures else DatasetState.QUARANTINED
    _, parquet_hash, count = export_parquet(bars, run_dir / "canonical-daily-bars.parquet")
    raw_frame = pd.DataFrame(raw_records).sort_values(["symbol", "timestamp"])
    raw_frame.to_parquet(run_dir / "normalized-raw-observations.parquet", compression="zstd", index=False)
    quality = {
        "critical_events": critical, "warning_events": sum(x.severity.value == "WARNING" for x in quality_events),
        "error_events": sum(x.severity.value == "ERROR" for x in quality_events),
        "quarantined_rows": len(quarantined), "request_failures": failures,
    }
    manifest = real_market_manifest(
        universe_manifest=universe, bars=bars, payload_hashes=[*payload_hashes, parquet_hash],
        mapping_hash=mapping_hash(mappings), created_at=started, state=state,
        collection_mode=CollectionMode.BACKFILLED_MARKET_DATA, quality_summary=quality,
        corporate_action_coverage={"attempted": len(symbols), "available": sum(isinstance(x, list) for x in corporate_actions.values()),
                                   "semantics": "PRICE_ADJUSTMENT_STATUS_UNVERIFIED"},
    )
    frames = []
    technical_snapshots = []
    analogue_snapshots = []
    for symbol in symbols:
        symbol_bars = [x for x in bars if x.symbol == symbol]
        if not symbol_bars:
            continue
        frame = frame_for_research(symbol_bars, datetime.now(UTC))
        frames.append(frame)
        features = build_feature_matrix(frame, information_cutoff=datetime.now(UTC),
                                        dataset_version=manifest["dataset_id"])
        complete = features.values.replace([np.inf, -np.inf], np.nan).dropna()
        technical_snapshots.append({"symbol": symbol, "cutoff": max(x.session_date for x in symbol_bars),
                                    "state": "REAL_MARKET_DATA_INTERNAL", "validation": "NOT_PREDICTIVELY_VALIDATED",
                                    "feature_set_hash": features.feature_set_hash,
                                    "complete_feature_rows": len(complete), "dataset_id": manifest["dataset_id"]})
        if len(complete) >= 30:
            cutoff = complete.index.get_level_values("session_date").max()
            states = complete.reset_index()
            feature_columns = [x for x in states.columns if x not in {"instrument_id", "session_date"}]
            analogue = find_analogues(
                states, query_instrument=str(matched[symbol].id), query_time=cutoff,
                feature_columns=feature_columns, k=min(10, len(complete) - 1),
                exclusion_sessions=10,
            )
            analogue_snapshots.append({"symbol": symbol, "cutoff": str(cutoff),
                                       "state": "REAL_MARKET_DATA_INTERNAL",
                                       "eligible_analogues": len(analogue.matches),
                                       "past_only": bool((analogue.matches["session_date"] < cutoff).all()),
                                       "dataset_id": manifest["dataset_id"]})
    (run_dir / "request-ledger.json").write_text(json.dumps(request_ledger, indent=2, default=str), encoding="utf-8")
    (run_dir / "corporate-actions.json").write_text(json.dumps(corporate_actions, indent=2, default=str), encoding="utf-8")
    (run_dir / "quality-events.json").write_text(
        json.dumps([x.model_dump(mode="json") for x in quality_events], indent=2, default=str),
        encoding="utf-8",
    )
    (run_dir / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    (run_dir / "technical-snapshots.json").write_text(
        json.dumps(technical_snapshots, indent=2, default=str), encoding="utf-8"
    )
    (run_dir / "historical-analogue-snapshots.json").write_text(
        json.dumps(analogue_snapshots, indent=2, default=str), encoding="utf-8"
    )
    summary = {"stage": stage, "auth": "HEALTHY", "market_status": status["status"],
               "mapping": {"total": len(expected), "matched": len(matched), "ambiguous": 0, "unmatched": 0},
               "symbols": len(symbols), "bars": count, "state": state, "quality": quality,
               "technical_snapshots": len(technical_snapshots), "analogue_snapshots": len(analogue_snapshots),
               "dataset_id": manifest["dataset_id"], "dataset_hash": manifest["dataset_hash"],
               "runtime_path": str(run_dir.relative_to(ROOT))}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True, default=str))
    return 0 if state == DatasetState.RESEARCH_ELIGIBLE else 4


if __name__ == "__main__":
    raise SystemExit(main())
