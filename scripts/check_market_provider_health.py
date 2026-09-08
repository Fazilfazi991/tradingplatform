from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from verified_edge.provider_health import (
    MarketProviderHealthLedger,
    check_market_provider,
)
from verified_edge.providers.upstox import UpstoxMarketDataProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "data/local/market-provider-health.sqlite3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitized read-only market-provider health")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--check", action="store_true")
    args = parser.parse_args()
    now = datetime.now(UTC)
    if args.status and not args.ledger.is_file():
        print(
            json.dumps(
                {
                    "provider": "UPSTOX",
                    "status": "NOT_CHECKED",
                    "checks": 0,
                    "credential_value_recorded": False,
                    "public_delivery": "BLOCKED",
                },
                sort_keys=True,
            )
        )
        return 0
    if args.check and not os.getenv("UPSTOX_ANALYTICS_TOKEN"):
        raise SystemExit("UPSTOX_ANALYTICS_TOKEN_ABSENT")
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger = MarketProviderHealthLedger(args.ledger)
    try:
        if args.check:
            ledger.append(check_market_provider(UpstoxMarketDataProvider(), now=now))
        report = ledger.report(now=now)
        print(json.dumps(report, sort_keys=True))
        return 0 if report["status"] in {"HEALTHY", "NOT_CHECKED"} else 2
    finally:
        ledger.close()


if __name__ == "__main__":
    raise SystemExit(main())
