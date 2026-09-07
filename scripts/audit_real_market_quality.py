"""Generate coverage, session, quarantine, and revision evidence for a real dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from verified_edge.real_market import observed_exchange_sessions


def main() -> int:
    run_dir = Path(sys.argv[1])
    bars = pd.read_parquet(run_dir / "canonical-daily-bars.parquet")
    raw = pd.read_parquet(run_dir / "normalized-raw-observations.parquet")
    quality_events = json.loads((run_dir / "quality-events.json").read_text(encoding="utf-8"))
    sessions = observed_exchange_sessions(bars)
    coverage = []
    missing_total = 0
    for symbol, group in bars.groupby("symbol"):
        present = set(pd.to_datetime(group.session_date).dt.date)
        relevant = {x for x in sessions if min(present) <= x <= max(present)}
        missing = len(relevant - present)
        missing_total += missing
        coverage.append({"symbol": symbol, "first_date": str(min(present)),
                         "last_date": str(max(present)), "bar_count": len(group),
                         "missing_observed_sessions": missing})
    duplicates = int(bars.duplicated(["instrument_id", "session_date"]).sum())
    report = {
        "calendar_method": "CONSENSUS_OBSERVED_NSE_EQ",
        "calendar_limitation": "Cannot detect an exchange-wide omission from the single provider",
        "observed_sessions": len(sessions), "coverage_by_symbol": coverage,
        "missing_observed_sessions": missing_total, "duplicate_canonical_bars": duplicates,
        "quarantined_rows": sum(x["severity"] == "CRITICAL" for x in quality_events),
        "warning_events": sum(x["severity"] == "WARNING" for x in quality_events),
        "raw_rows": len(raw), "canonical_rows": len(bars),
        "stale_state": "NOT_APPLICABLE_TO_BACKFILL",
        "independent_calendar_source": "NOT_CONFIGURED",
    }
    (run_dir / "data-quality-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "observed_sessions", "missing_observed_sessions", "duplicate_canonical_bars",
        "quarantined_rows", "raw_rows", "canonical_rows")}, sort_keys=True))
    return 0 if not duplicates else 2


if __name__ == "__main__":
    raise SystemExit(main())
