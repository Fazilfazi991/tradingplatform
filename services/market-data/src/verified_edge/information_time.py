from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from verified_edge.domain import InformationEvent


def events_available_at(
    events: Iterable[InformationEvent], decision_time: datetime
) -> list[InformationEvent]:
    """Return only information genuinely available at the decision boundary."""
    if decision_time.tzinfo is None or decision_time.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    return sorted(
        (event for event in events if event.available_at <= decision_time),
        key=lambda event: (event.available_at, str(event.id)),
    )
