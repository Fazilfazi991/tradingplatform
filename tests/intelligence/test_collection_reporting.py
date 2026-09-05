from datetime import UTC, datetime, timedelta

from intelligence_core.runtime_forensics import (
    CollectionAttemptRecord,
    ForensicRuntimeStore,
    derive_collection_report,
)

NOW = datetime(2026, 9, 4, tzinfo=UTC)


def row(
    *,
    job: str,
    source: str,
    ordinal: int = 1,
    transport: str = "SUCCEEDED",
    handler: str = "SUCCEEDED",
    parse: str = "PASS",
    terminal: str = "SUCCEEDED",
    recovered: bool = False,
    offset: int = 0,
) -> CollectionAttemptRecord:
    started = NOW + timedelta(minutes=offset)
    return CollectionAttemptRecord(
        job_id=job,
        source_id=source,
        scheduled_for=started,
        started_at=started,
        completed_at=started + timedelta(seconds=1),
        attempt_ordinal=ordinal,
        transport_status=transport,
        error_class="Timeout" if transport == "FAILED" else None,
        handler_status=handler,
        parse_status=parse,
        records_seen=10 if terminal == "SUCCEEDED" else 0,
        canonical_events=2 if terminal == "SUCCEEDED" else 0,
        duplicate_count=8 if terminal == "SUCCEEDED" else 0,
        recovered=recovered,
        terminal_job_status=terminal,
        latency_ms=1000,
        provenance_hash=f"{job}-{ordinal}",
    )


def test_outer_success_and_collector_success_has_no_terminal_failure(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "a.sqlite3")
    store.add_collection_attempt(row(job="rbi:1", source="rbi"))
    report = derive_collection_report(
        store, outer_execution_statuses=["SUCCEEDED"], canonical_event_inventory=2
    )
    assert report["terminal_failures"] == report["source_failures"] == 0
    assert report["outer_worker_failures"] == 0
    store.close()


def test_failed_attempt_recovered_in_same_job_is_not_terminal(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "b.sqlite3")
    store.add_collection_attempt(
        row(
            job="sebi:1",
            source="sebi",
            transport="FAILED",
            handler="FAILED",
            parse="NOT_RUN",
            terminal="PENDING",
        )
    )
    store.add_collection_attempt(row(job="sebi:1", source="sebi", ordinal=2, recovered=True))
    report = store.collection_reconciliation()
    assert report["failed_attempts"] == report["recovered_failures"] == 1
    assert report["terminal_failures"] == report["source_failures"] == 0
    store.close()


def test_outer_success_does_not_mask_terminal_collector_failure(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "c.sqlite3")
    store.add_collection_attempt(
        row(
            job="rbi:1",
            source="rbi",
            transport="FAILED",
            handler="FAILED",
            parse="NOT_RUN",
            terminal="FAILED",
        )
    )
    report = derive_collection_report(
        store, outer_execution_statuses=["SUCCEEDED"], canonical_event_inventory=0
    )
    assert report["failed_attempts"] == 1
    assert report["terminal_failures"] == report["source_failures"] == 1
    assert report["outer_worker_failures"] == 0
    store.close()


def test_outer_worker_failure_remains_a_separate_metric(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "d.sqlite3")
    store.add_collection_attempt(row(job="rbi:1", source="rbi"))
    report = derive_collection_report(
        store, outer_execution_statuses=["FAILED"], canonical_event_inventory=2
    )
    assert report["outer_worker_failures"] == 1
    assert report["terminal_failures"] == 0
    store.close()


def test_mixed_sources_reconcile_exactly(tmp_path):
    store = ForensicRuntimeStore(tmp_path / "e.sqlite3")
    store.add_collection_attempt(row(job="rbi:1", source="rbi"))
    store.add_collection_attempt(
        row(
            job="sebi:1",
            source="sebi",
            transport="FAILED",
            handler="FAILED",
            parse="NOT_RUN",
            terminal="PENDING",
            offset=1,
        )
    )
    store.add_collection_attempt(
        row(job="sebi:1", source="sebi", ordinal=2, recovered=True, offset=1)
    )
    report = store.collection_reconciliation()
    for field in (
        "scheduled_executions",
        "attempts",
        "failed_attempts",
        "recovered_failures",
        "terminal_failures",
        "records_seen",
        "canonical_events",
        "duplicates",
    ):
        assert report[field] == sum(source[field] for source in report["by_source"].values())
    assert report["scheduled_executions"] == 2
    store.close()
