from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.live_activation import LiveEngineStatus, daily_live_report


def main() -> None:
    source_path = Path("research/intelligence/live-source-validation.json")
    validation = json.loads(source_path.read_text(encoding="utf-8"))
    sources = validation["sources"]
    seen = sum(source["records_seen"] for source in sources.values())
    canonical = sum(source["records_new"] for source in sources.values())
    duplicates = sum(source["duplicates"] for source in sources.values())
    report = daily_live_report(
        report_date=datetime.now(UTC).date(),
        live_sources={name: source["source_health"] for name, source in sources.items()},
        records=[],
        events_seen=seen,
        canonical_events=canonical,
        duplicates=duplicates,
        unknown_events=canonical,
        entity_counts={"matched": 0, "unmatched": canonical, "ambiguous": 0, "multi_entity": 0},
        engine_states={
            "news_event": LiveEngineStatus.LIVE,
            "macro": LiveEngineStatus.LIVE,
            "psychology": LiveEngineStatus.INSUFFICIENT,
            "fundamental": LiveEngineStatus.ENGINEERING_ONLY,
            "flow_derivatives": LiveEngineStatus.INSUFFICIENT,
            "technical": LiveEngineStatus.ENGINEERING_ONLY,
            "historical": LiveEngineStatus.ENGINEERING_ONLY,
        },
        incidents=[],
    )
    report["llm_status"] = "NO_PROVIDER_CONFIGURED_UNKNOWN_ONLY"
    report["macro_state"] = "UNKNOWN"
    report["psychology_state"] = "INSUFFICIENT_PSYCHOLOGY_EVIDENCE"
    report["fusion_state"] = "ABSTAIN"
    target = Path("research/intelligence/daily-live-intelligence-report.json")
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
