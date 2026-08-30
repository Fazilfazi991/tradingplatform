"""Validate current NIFTY 200 symbols against Upstox's public instrument master.

Bulk provider/index payloads are processed in memory and are never committed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from verified_edge.providers.upstox import UpstoxMarketDataProvider

SOURCE_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
OUTPUT = Path("data/manifests/current_nifty200_mapping.json")


def main() -> None:
    request = Request(SOURCE_URL, headers={"User-Agent": "VerifiedEdge/0.1 internal QA"})
    with urlopen(request, timeout=30) as response:
        payload = response.read()
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    symbols = [row["Symbol"].strip() for row in rows]
    instruments = UpstoxMarketDataProvider().get_instruments()

    mapped: dict[str, dict[str, str | None]] = {}
    unmapped: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    inactive: list[str] = []
    for symbol in symbols:
        matches = [
            item
            for item in instruments
            if item.symbol == symbol
            and item.exchange == "NSE"
            and item.segment == "NSE_EQ"
            and item.instrument_type in {"EQ", "EQUITY"}
        ]
        if not matches:
            unmapped.append(symbol)
        elif len(matches) > 1:
            ambiguous[symbol] = sorted(item.provider_instrument_key or "" for item in matches)
        else:
            item = matches[0]
            if item.listing_status != "ACTIVE":
                inactive.append(symbol)
            mapped[symbol] = {
                "exchange": item.exchange,
                "isin": item.isin,
                "internal_instrument_id": str(item.id),
                "provider_instrument_key": item.provider_instrument_key,
            }

    duplicate_symbols = sorted({symbol for symbol in symbols if symbols.count(symbol) > 1})
    report = {
        "scope": "CURRENT INGESTION TESTING ONLY; not point-in-time membership",
        "source": SOURCE_URL,
        "fetched_at": datetime.now(UTC).isoformat(),
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "total": len(symbols),
        "mapped": len(mapped),
        "unmapped": unmapped,
        "ambiguous": ambiguous,
        "duplicates": duplicate_symbols,
        "inactive": inactive,
        "mapping_rate_percent": round(100 * len(mapped) / len(symbols), 4) if symbols else 0,
        "mappings": mapped,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "mappings"}, indent=2))


if __name__ == "__main__":
    main()
