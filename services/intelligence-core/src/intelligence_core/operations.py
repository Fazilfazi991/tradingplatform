from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from research_core.common import stable_hash

from intelligence_core.models import HealthStatus, InformationEvent, IntelligenceIncident
from intelligence_core.processing import cluster_events
from intelligence_core.snapshot import build_intelligence_snapshot


def event_priority(
    event: InformationEvent, *, reliability: float, novelty: float, entity_relevance: float
) -> str:
    importance = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "MATERIAL": 3}[event.importance]
    score = importance + reliability + novelty + entity_relevance
    if event.quality_status != "PASS":
        return "URGENT_REVIEW"
    if score >= 5:
        return "MATERIAL"
    if score >= 3.5:
        return "HIGH"
    if score >= 2:
        return "NORMAL"
    return "LOW"


def daily_summary(
    day: date,
    events: list[InformationEvent],
    source_health: dict[str, HealthStatus],
    incidents: list[dict[str, Any]],
    unresolved_entities: int = 0,
) -> dict[str, Any]:
    selected = [event for event in events if event.available_at.date() == day]
    clusters = cluster_events(selected)
    return {
        "date": day.isoformat(),
        "sources_healthy": sum(v == HealthStatus.HEALTHY for v in source_health.values()),
        "sources_degraded": sum(v != HealthStatus.HEALTHY for v in source_health.values()),
        "events_collected": len(selected),
        "new_events": len(clusters),
        "duplicates_suppressed": sum(max(0, len(group) - 1) for group in clusters.values()),
        "material_events": sum(event.importance == "MATERIAL" for event in selected),
        "companies_affected": len({event.entity_id for event in selected if event.entity_id}),
        "sectors_affected": len(
            {
                event.metadata_json.get("sector")
                for event in selected
                if event.metadata_json.get("sector")
            }
        ),
        "macro_events": sum(event.entity_type.startswith("MACRO") for event in selected),
        "unresolved_entities": unresolved_entities,
        "corrections": sum(event.correction_of is not None for event in selected),
        "source_incidents": len([item for item in incidents if item.get("status") == "OPEN"]),
        "prediction": "NOT_PRODUCED",
    }


def semantic_event(event: InformationEvent) -> dict[str, Any]:
    return {
        "source_id": event.source_id,
        "source_event_id": event.source_event_id,
        "entity_id": event.entity_id,
        "event_type": event.event_type,
        "title": event.title,
        "published_at": event.published_at.isoformat(),
        "observed_at": event.observed_at.isoformat(),
        "available_at": event.available_at.isoformat(),
        "raw_payload_hash": event.raw_payload_hash,
        "collection_origin": event.collection_origin,
    }


def build_daily_archive(
    day: date,
    *,
    events: list[InformationEvent],
    source_health: dict[str, HealthStatus],
    job_ids: list[str],
    incidents: list[dict[str, Any]],
    universe_state: dict[str, Any],
    target: str | Path,
) -> dict[str, Any]:
    selected = sorted(
        (semantic_event(event) for event in events if event.available_at.date() == day),
        key=lambda item: (item["available_at"], item["source_id"], item["title"]),
    )
    clusters = cluster_events([event for event in events if event.available_at.date() == day])
    snapshots = {}
    entities = sorted({event.entity_id for event in events if event.entity_id})
    cutoff = (
        datetime.combine(day, datetime.max.time(), tzinfo=events[0].available_at.tzinfo)
        if events
        else None
    )
    if cutoff:
        snapshots = {
            entity: build_intelligence_snapshot(entity, cutoff, events).snapshot_hash
            for entity in entities
        }
    payload = {
        "date": day.isoformat(),
        "sources": {key: str(value) for key, value in sorted(source_health.items())},
        "job_ids": sorted(job_ids),
        "events": selected,
        "clusters": sorted(
            stable_hash([semantic_event(item) for item in group]) for group in clusters.values()
        ),
        "snapshots": snapshots,
        "incidents": incidents,
        "universe_state": universe_state,
    }
    payload["manifest_hash"] = stable_hash(payload)
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise FileExistsError("daily archive is immutable")
        return existing
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return payload


def replay_semantic_hash(events: list[InformationEvent]) -> str:
    return stable_hash(
        sorted(
            (semantic_event(event) for event in events),
            key=lambda item: (item["source_id"], item["source_event_id"] or "", item["title"]),
        )
    )


def health_incidents(
    source_id: str, *, status: HealthStatus, evidence: dict[str, Any]
) -> list[IntelligenceIncident]:
    if status == HealthStatus.HEALTHY:
        return []
    if status == HealthStatus.STALE:
        incident = IntelligenceIncident(
            incident_type="SOURCE_STALE",
            severity="WARNING",
            source_id=source_id,
            evidence=evidence,
            affected_data=(source_id,),
        )
    else:
        incident = IntelligenceIncident(
            incident_type="PARSER_SCHEMA_CHANGE",
            severity="HIGH" if status == HealthStatus.FAILING else "WARNING",
            source_id=source_id,
            evidence=evidence,
            affected_data=(source_id,),
        )
    return [incident]
