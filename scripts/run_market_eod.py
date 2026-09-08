from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from verified_edge.eod import EodCollector, EodConfig, EodLedger
from verified_edge.providers.upstox import UpstoxMarketDataProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/market-data-eod.json"
DEFAULT_UNIVERSE = ROOT / "data/manifests/current_nifty200_mapping.json"
DEFAULT_LEDGER = ROOT / "data/local/market-data-eod.sqlite3"


def load_config(path: Path) -> EodConfig:
    return EodConfig.model_validate_json(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Internal read-only market-data EOD operation")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--run", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.status:
        ledger_report = {
            "status": "NOT_STARTED",
            "runs": 0,
            "bars": 0,
            "public_delivery": "BLOCKED",
        }
        if args.ledger.is_file():
            ledger = EodLedger(args.ledger)
            try:
                ledger_report = ledger.report()
            finally:
                ledger.close()
        print(
            json.dumps(
                {
                    "execution_operations": config.execution_operations,
                    "collection_mode": config.collection_mode,
                    **ledger_report,
                },
                sort_keys=True,
            )
        )
        return 0
    if not config.execution_operations:
        raise SystemExit("MARKET_DATA_EOD_DISABLED")
    token = os.getenv(config.credential)
    if not token:
        raise SystemExit("UPSTOX_ANALYTICS_TOKEN_ABSENT")
    universe = json.loads(args.universe.read_text(encoding="utf-8"))["mappings"]
    provider = UpstoxMarketDataProvider(token=token)
    collector = EodCollector(provider, config, universe)
    now = datetime.now(UTC)
    session_date = now.astimezone(ZoneInfo(config.timezone)).date()
    run, bars = collector.collect(session_date, now=now)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger = EodLedger(args.ledger)
    try:
        ledger.append(run, bars)
        print(json.dumps(ledger.report(), sort_keys=True))
    finally:
        ledger.close()
    return 0 if run.state == "COMPLETE" else 4


if __name__ == "__main__":
    raise SystemExit(main())
