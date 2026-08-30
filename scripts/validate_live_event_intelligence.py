from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.catalog import initial_sources
from intelligence_core.collectors import OfficialRssCollector
from intelligence_core.event_intelligence import DeterministicEventAnalyzer
from intelligence_core.live import FEEDS
from intelligence_core.models import (
    CollectionPolicy,
    IntelligenceRuntimeMode,
    IntelligenceRuntimePolicy,
)
from intelligence_core.news_evidence import qa_metrics


def main() -> None:
    IntelligenceRuntimePolicy.authorize(IntelligenceRuntimeMode.INTERNAL_LIVE)
    analyzer = DeterministicEventAnalyzer()
    report = {
        "label": "INTERNAL EVENT EVIDENCE — NOT PREDICTION",
        "analyzer": analyzer.version,
        "llm_status": "DISABLED_NO_CREDENTIALS",
        "started_at": datetime.now(UTC).isoformat(),
        "sources": {},
    }
    for source in initial_sources():
        started = time.perf_counter()
        collector = OfficialRssCollector(
            source,
            CollectionPolicy(source_id=source.source_id, cadence_seconds=900),
            FEEDS[source.source_id],
        )
        artifact = collector.fetch(collector.discover()[0])
        events = collector.normalize(collector.parse(artifact), artifact)
        records = [
            analyzer.analyze(
                event,
                cluster_id=str(event.event_id),
                derived_at=max(datetime.now(UTC), event.available_at),
            )
            for event in events
        ]
        metrics = qa_metrics(records, len(events))
        report["sources"][source.source_id] = {
            "events_processed": len(records),
            "event_types": dict(
                sorted(
                    {
                        kind: sum(record.event_type == kind for record in records)
                        for kind in {record.event_type for record in records}
                    }.items()
                )
            ),
            "material_events": sum(
                record.materiality in {"MATERIAL", "SYSTEMIC"} for record in records
            ),
            "official_confirmed": sum(
                record.confirmation_state == "OFFICIAL_CONFIRMED" for record in records
            ),
            "entity_matches": sum(record.primary_entity_id is not None for record in records),
            "sector_matches": sum(bool(record.affected_sectors) for record in records),
            "qa": metrics,
            "processing_latency_seconds": time.perf_counter() - started,
            "samples": [
                {
                    "title": record.summary[:160],
                    "event_type": record.event_type,
                    "materiality": record.materiality,
                    "direction": record.direction,
                    "confirmation": record.confirmation_state,
                    "status": record.status,
                    "available_at": record.available_at.isoformat(),
                }
                for record in records[:3]
            ],
        }
    report["ended_at"] = datetime.now(UTC).isoformat()
    target = Path("research/intelligence/live-event-intelligence-validation.json")
    target.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
