"""Validate a completed real-market dataset without exposing provider data publicly."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
from research_core.targets import build_targets
from verified_edge.domain import Instrument
from verified_edge.providers.upstox import UpstoxMarketDataProvider

ROOT = Path(__file__).resolve().parents[1]


def token() -> str:
    if os.getenv("UPSTOX_ANALYTICS_TOKEN"):
        return os.environ["UPSTOX_ANALYTICS_TOKEN"]
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("UPSTOX_ANALYTICS_TOKEN="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("UPSTOX_ANALYTICS_TOKEN missing")


def main() -> int:
    run_dir = Path(sys.argv[1])
    frame = pd.read_parquet(run_dir / "canonical-daily-bars.parquet")
    frame[["open", "high", "low", "close"]] = frame[["open", "high", "low", "close"]].astype(float)
    targets = build_targets(frame, horizons=(1, 3, 5, 10)).values.reset_index()
    latest_checks = {}
    for instrument_id, group in targets.groupby("instrument_id"):
        latest = group.sort_values("session_date").iloc[-1]
        latest_checks[instrument_id] = all(pd.isna(latest[f"target_forward_return_{h}"]) for h in (1, 3, 5, 10))
    universe = json.loads((ROOT / "data/manifests/current_nifty200_mapping.json").read_text(encoding="utf-8"))
    provider = UpstoxMarketDataProvider(token=token())
    quotes = []
    for symbol in ("RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK"):
        item = universe["mappings"][symbol]
        instrument = Instrument(exchange="NSE", segment="NSE_EQ", symbol=symbol,
                                isin=item["isin"], provider_instrument_key=item["provider_instrument_key"])
        response = provider.get_quote(instrument).get("data", {})
        quote = next(iter(response.values())) if response else {}
        latest_close = float(frame.loc[frame.symbol == symbol].sort_values("session_date").iloc[-1].close)
        reference = quote.get("cp")
        quotes.append({"symbol": symbol, "latest_completed_close": latest_close,
                       "provider_previous_close": reference,
                       "consistent": reference is not None and abs(latest_close - float(reference)) < 0.01})
    report = {
        "target_rows": len(targets), "target_horizons": [1, 3, 5, 10],
        "latest_rows_without_future_targets": sum(latest_checks.values()),
        "latest_rows_checked": len(latest_checks), "leakage_check": all(latest_checks.values()),
        "quote_consistency": quotes, "independent_second_source": "NOT_CONFIGURED",
        "result_label": "REAL_BACKFILLED_MARKET_DATA", "prediction_model": "NOT_STARTED",
    }
    (run_dir / "real-dataset-validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({"target_rows": report["target_rows"], "leakage_check": report["leakage_check"],
                      "quote_consistent": sum(x["consistent"] for x in quotes),
                      "quotes_checked": len(quotes)}, sort_keys=True))
    return 0 if report["leakage_check"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
