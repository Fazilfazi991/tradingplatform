from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from research_core.common import stable_hash

from intelligence_core.models import HealthStatus, InformationEvent, NoveltyScore


def content_fingerprint(event: InformationEvent) -> str:
    words = sorted(set(re.findall(r"[a-z0-9]+", f"{event.title} {event.summary}".lower())))
    return stable_hash({"entity": event.entity_id, "type": event.event_type, "words": words})


def cluster_events(
    events: list[InformationEvent], *, window: timedelta = timedelta(hours=24)
) -> dict[str, list[InformationEvent]]:
    clusters: dict[str, list[InformationEvent]] = {}
    for event in sorted(events, key=lambda item: (item.available_at, str(item.event_id))):
        identifier = None
        event_words = set(re.findall(r"[a-z0-9]+", event.title.lower()))
        for cluster_id, members in clusters.items():
            anchor = members[0]
            anchor_words = set(re.findall(r"[a-z0-9]+", anchor.title.lower()))
            similarity = len(event_words & anchor_words) / max(1, len(event_words | anchor_words))
            if (event.source_event_id and event.source_event_id == anchor.source_event_id) or (
                event.entity_id == anchor.entity_id
                and event.event_type == anchor.event_type
                and abs(event.published_at - anchor.published_at) <= window
                and similarity >= 0.45
            ):
                identifier = cluster_id
                break
        identifier = identifier or stable_hash({"event": str(event.event_id)})[:16]
        clusters.setdefault(identifier, []).append(event)
    return clusters


def novelty(event: InformationEvent, cluster: list[InformationEvent]) -> NoveltyScore:
    if event.correction_of:
        return NoveltyScore(state="CORRECTION", score=1, evidence=("correction_of",))
    if event.metadata_json.get("rumour"):
        return NoveltyScore(state="RUMOUR", score=0.2, evidence=("rumour flag",))
    if len(cluster) == 1:
        return NoveltyScore(state="NEW", score=1, evidence=("first cluster record",))
    if event.source_event_id and any(
        item.source_event_id == event.source_event_id for item in cluster[:-1]
    ):
        return NoveltyScore(state="DUPLICATE", score=0, evidence=("same source event id",))
    return NoveltyScore(state="FOLLOW_UP", score=0.3, evidence=("same entity/type/time cluster",))


@dataclass
class CircuitBreaker:
    threshold: int = 3
    failures: int = 0
    opened: bool = False

    def record_success(self) -> None:
        self.failures = 0
        self.opened = False

    def record_failure(self) -> None:
        self.failures += 1
        self.opened = self.failures >= self.threshold

    @property
    def health(self) -> HealthStatus:
        if self.opened:
            return HealthStatus.FAILING
        if self.failures:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


def append_correction(
    events: list[InformationEvent], corrected: InformationEvent
) -> list[InformationEvent]:
    if not corrected.correction_of or not any(
        item.event_id == corrected.correction_of for item in events
    ):
        raise ValueError("correction must reference an existing event")
    if corrected.available_at <= next(
        item.available_at for item in events if item.event_id == corrected.correction_of
    ):
        raise ValueError("correction must become available later")
    return [*events, corrected]


def source_health(
    *,
    last_success: datetime | None,
    now: datetime,
    expected_freshness: timedelta,
    failure_rate: float,
    schema_failures: int,
    disabled: bool = False,
) -> HealthStatus:
    if disabled:
        return HealthStatus.DISABLED
    if schema_failures >= 3 or failure_rate >= 0.5:
        return HealthStatus.FAILING
    if last_success is None:
        return HealthStatus.UNKNOWN
    if now - last_success > expected_freshness:
        return HealthStatus.STALE
    if failure_rate > 0 or schema_failures > 0:
        return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY
