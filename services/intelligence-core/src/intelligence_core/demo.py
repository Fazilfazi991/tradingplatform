from __future__ import annotations

from datetime import UTC, datetime

from intelligence_core.fixtures import demo_timeline
from intelligence_core.processing import cluster_events
from intelligence_core.snapshot import build_intelligence_snapshot


def main() -> None:
    events = demo_timeline()
    cutoff = datetime(2026, 8, 28, 14, tzinfo=UTC)
    snapshot = build_intelligence_snapshot("DEMO_RELIANCE", cutoff, events)
    clusters = cluster_events(list(snapshot.events))
    duplicates = sum(max(0, len(records) - 1) for records in clusters.values())
    material = sum(event.importance == "MATERIAL" for event in snapshot.events)
    directions = {event.direction for event in snapshot.events}
    contradictions = int("POSITIVE" in directions and "NEGATIVE" in directions)
    print("Entity: DEMO_RELIANCE")
    print("Cutoff: 2026-08-28 14:00 UTC")
    print(f"Sources: {len(snapshot.source_ids)}")
    print(f"Raw observations: {len(snapshot.events)}")
    print(f"Canonical event clusters: {len(clusters)}")
    print(f"Duplicate stories suppressed: {duplicates}")
    print(f"Material events: {material}")
    print(f"Contradictions: {contradictions}")
    print("Source health: HEALTHY (fixture)")
    print("Prediction: NOT PRODUCED")
