from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from verified_edge.domain import InformationEvent
from verified_edge.information_time import events_available_at


def event(**updates):
    published = datetime(2026, 1, 1, 12, tzinfo=UTC)
    values = {
        "entity_id": uuid4(),
        "event_type": "NEWS",
        "source_id": uuid4(),
        "value": {"x": 1},
        "event_time": published,
        "published_at": published,
        "observed_at": published + timedelta(seconds=2),
        "available_at": published + timedelta(seconds=3),
        "raw_artifact_uri": "s3://raw/a",
        "source_version": "1",
    }
    values.update(updates)
    return InformationEvent(**values)


def test_information_time_accepts_causal_timestamps():
    assert event().available_at >= event().published_at


def test_information_cannot_be_available_before_publication():
    published = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with pytest.raises(ValidationError):
        event(published_at=published, available_at=published - timedelta(seconds=1))


def test_naive_information_timestamps_rejected():
    naive_timestamp = datetime.fromisoformat("2026-01-01T12:00:00")
    with pytest.raises(ValidationError):
        event(event_time=naive_timestamp)


def test_decision_boundary_excludes_future_available_information():
    decision_time = datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)
    known = event(available_at=decision_time)
    future = event(available_at=decision_time + timedelta(microseconds=1))
    assert events_available_at([future, known], decision_time) == [known]


def test_decision_boundary_requires_timezone():
    with pytest.raises(ValueError, match="timezone-aware"):
        events_available_at([event()], datetime.fromisoformat("2026-01-01T12:00:00"))
