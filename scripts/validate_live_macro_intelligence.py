from __future__ import annotations

import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.live import FEEDS
from intelligence_core.macro import classify_rbi_event, default_unknown_state
from intelligence_core.models import (
    CollectionPolicy,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)


def main() -> None:
    IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.INTERNAL_LIVE)
    source = next(item for item in initial_sources() if item.source_id == "rbi-press-releases-rss")
    collector = OfficialRssCollector(
        source,
        CollectionPolicy(source_id=source.source_id, cadence_seconds=900),
        FEEDS[source.source_id],
    )
    started = time.perf_counter()
    artifact = collector.fetch(collector.discover()[0])
    events = collector.normalize(collector.parse(artifact), artifact)
    categories = [classify_rbi_event(event.title, event.summary) for event in events]
    policy, cross_market, regime = default_unknown_state(datetime.now(UTC))
    report = {
        "label": "INTERNAL MACRO EVIDENCE — NOT PREDICTION",
        "source": source.source_id,
        "events_processed": len(events),
        "classifications": dict(sorted(Counter(categories).items())),
        "numeric_observations": 0,
        "policy_state": policy.model_dump(mode="json"),
        "cross_market_state": cross_market.model_dump(mode="json"),
        "regime": regime.model_dump(mode="json"),
        "unknown_policy_state": True,
        "entity_associations": 0,
        "processing_latency_seconds": time.perf_counter() - started,
        "llm_status": "DISABLED_NO_CREDENTIALS",
        "observed_at": datetime.now(UTC).isoformat(),
        "samples": [
            {
                "title": event.title[:160],
                "classification": category,
                "available_at": event.available_at.isoformat(),
            }
            for event, category in zip(events[:3], categories[:3], strict=True)
        ],
    }
    target = Path("research/intelligence/live-macro-intelligence-validation.json")
    target.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
