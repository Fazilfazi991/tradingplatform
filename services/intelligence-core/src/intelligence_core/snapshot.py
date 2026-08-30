from __future__ import annotations

from datetime import datetime

from intelligence_core.models import InformationEvent, IntelligenceSnapshot


def build_intelligence_snapshot(
    entity_id: str, cutoff: datetime, events: list[InformationEvent]
) -> IntelligenceSnapshot:
    eligible = tuple(
        sorted(
            (
                event
                for event in events
                if event.available_at <= cutoff
                and (
                    event.entity_id in {None, entity_id}
                    or entity_id in event.metadata_json.get("related_entities", [])
                )
            ),
            key=lambda event: (event.available_at, str(event.event_id)),
        )
    )
    source_ids = tuple(sorted({event.source_id for event in eligible}))
    quality = tuple(sorted({event.quality_status for event in eligible}))
    usable = [event for event in eligible if event.quality_status == "PASS"]
    return IntelligenceSnapshot(
        entity_id=entity_id,
        cutoff=cutoff,
        events=eligible,
        source_ids=source_ids,
        quality_states=quality,
        abstention="SUFFICIENT" if usable else "INSUFFICIENT_INTELLIGENCE",
    )
