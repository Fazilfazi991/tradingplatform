from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from verified_edge.providers.upstox import AuthenticationError, UpstoxMarketDataProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Verified Edge read-only data tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("upstox-health", help="read-only authenticated health check")
    spike = sub.add_parser("upstox-spike", help="fetch daily candles; never places orders")
    spike.add_argument(
        "--symbols",
        required=True,
        help="comma-separated NSE symbols; recommended first stage: five",
    )
    spike.add_argument("--start", required=True, type=date.fromisoformat)
    spike.add_argument("--end", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    provider = UpstoxMarketDataProvider()
    try:
        if args.command == "upstox-health":
            print(provider.health_check())
            return 0
        if args.command == "upstox-spike":
            if not os.getenv("UPSTOX_ACCESS_TOKEN"):
                raise AuthenticationError("UPSTOX_ACCESS_TOKEN is absent; live spike not run")
            for symbol in args.symbols.split(","):
                instrument = provider.resolve_instrument(symbol.strip().upper())
                rows = provider.get_historical_daily(instrument, args.start, args.end)
                print({"symbol": symbol, "rows": len(rows)})
            return 0
    except AuthenticationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
