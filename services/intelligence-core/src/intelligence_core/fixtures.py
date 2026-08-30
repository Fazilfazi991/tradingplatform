from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from research_core.common import stable_hash

from intelligence_core.entities import Entity
from intelligence_core.models import EventType, InformationEvent


def demo_entity() -> Entity:
    return Entity(
        "DEMO_RELIANCE",
        "Demo Reliance Industries Limited",
        "INE-DEMO-001",
        ("DEMO_RELIANCE", "DEMO-RIL"),
        ("Demo Reliance", "Demo RIL"),
    )


def demo_timeline() -> list[InformationEvent]:
    day = datetime(2026, 8, 28, tzinfo=UTC)
    return [
        _event(
            "macro",
            None,
            EventType.MACRO_RELEASE,
            "Positive macro development",
            day.replace(hour=9),
            direction="POSITIVE",
            related=["DEMO_RELIANCE"],
        ),
        _event(
            "filing",
            "DEMO_RELIANCE",
            EventType.CONTRACT,
            "Demo Reliance wins material contract",
            day.replace(hour=10, minute=20),
            importance="MATERIAL",
            direction="POSITIVE",
        ),
        _event(
            "news1",
            "DEMO_RELIANCE",
            EventType.CONTRACT,
            "Material contract won by Demo Reliance",
            day.replace(hour=10, minute=26),
            direction="POSITIVE",
        ),
        _event(
            "news2",
            "DEMO_RELIANCE",
            EventType.CONTRACT,
            "Demo Reliance wins material contract",
            day.replace(hour=11, minute=5),
            direction="POSITIVE",
        ),
        _event(
            "sector",
            None,
            EventType.SECTOR_POLICY,
            "Energy sector faces adverse policy change",
            day.replace(hour=13, minute=30),
            direction="NEGATIVE",
            related=["DEMO_RELIANCE"],
        ),
        _event(
            "earnings",
            "DEMO_RELIANCE",
            EventType.EARNINGS,
            "Demo Reliance post-close earnings",
            day.replace(hour=16, minute=15),
            importance="MATERIAL",
            direction="MIXED",
        ),
    ]


def _event(
    key: str,
    entity: str | None,
    event_type: EventType,
    title: str,
    published: datetime,
    *,
    importance: Literal["LOW", "MEDIUM", "HIGH", "MATERIAL"] = "MEDIUM",
    direction: Literal["POSITIVE", "NEGATIVE", "MIXED", "NEUTRAL", "UNKNOWN"] = "UNKNOWN",
    related: list[str] | None = None,
) -> InformationEvent:
    return InformationEvent(
        entity_id=entity,
        entity_type="COMPANY" if entity else "MACRO_OR_SECTOR",
        source_id=f"fixture-{key}",
        source_event_id=key,
        event_type=event_type,
        title=title,
        summary=title,
        raw_artifact_uri=f"fixture://{key}",
        raw_payload_hash=stable_hash(title),
        event_time=published,
        published_at=published,
        observed_at=published,
        available_at=published,
        importance=importance,
        direction=direction,
        metadata_json={"related_entities": related or []},
    )
