from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.models import (
    CollectionMode,
    CollectionPolicy,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)
from intelligence_core.scheduler import CollectionRunner

FEEDS = {
    "rbi-press-releases-rss": "https://rbi.org.in/pressreleases_rss.xml",
    "sebi-rss": "https://www.sebi.gov.in/sebirss.xml",
}


def main() -> None:
    IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.INTERNAL_LIVE)
    report = {
        "label": "INTERNAL SOURCE HEALTH — NOT CUSTOMER CONTENT",
        "started_at": datetime.now(UTC).isoformat(),
        "cycles_requested": 3,
        "sources": {},
    }
    for source in initial_sources():
        runner = CollectionRunner()
        policy = CollectionPolicy(
            source_id=source.source_id,
            cadence_seconds=900,
            maximum_requests=1,
            retries=2,
            timeout_seconds=15,
            maximum_bytes=2_000_000,
            failure_threshold=3,
        )
        collector = OfficialRssCollector(source, policy, FEEDS[source.source_id])
        cycles = []
        started = time.perf_counter()
        for number in range(3):
            entry = runner.run(collector, policy, mode=CollectionMode.LIVE)
            cycles.append(entry.model_dump(mode="json"))
            if number < 2:
                time.sleep(1)
        events = list(runner.events.values())
        sample = [
            {
                "source": event.source_id,
                "title": event.title[:160],
                "published_at": event.published_at.isoformat(),
                "observed_at": event.observed_at.isoformat(),
                "event_type": event.event_type,
                "entity_match": "UNMATCHED",
                "novelty": "NEW",
            }
            for event in events[:3]
        ]
        report["sources"][source.source_id] = {
            "cycles": cycles,
            "records_seen": sum(c.records_seen for c in runner.ledger),
            "records_new": sum(c.records_new for c in runner.ledger),
            "duplicates": sum(c.records_duplicate for c in runner.ledger),
            "failures": sum(c.records_failed for c in runner.ledger),
            "source_health": runner.breakers[source.source_id].health,
            "duration_seconds": time.perf_counter() - started,
            "sample_metadata": sample,
        }
    report["ended_at"] = datetime.now(UTC).isoformat()
    target = Path("research/intelligence/live-source-validation.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
