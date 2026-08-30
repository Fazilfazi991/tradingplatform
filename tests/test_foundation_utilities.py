from datetime import date
from pathlib import Path

from test_dataset import bar
from test_pipeline import instrument
from verified_edge.logging import log_event
from verified_edge.reconciliation import reconcile
from verified_edge.storage import LocalArtifactStore
from verified_edge.universe import NIFTY200_V1, evaluate_eligibility


def test_local_artifacts_are_immutable(tmp_path):
    store = LocalArtifactStore(tmp_path)
    uri = store.put_json("raw/a.json", {"b": 2, "a": 1})
    assert Path(uri).exists() and store.get_json("raw/a.json") == {"a": 1, "b": 2}
    try:
        store.put_json("raw/a.json", {"a": 2})
        raise AssertionError("immutable overwrite was accepted")
    except FileExistsError:
        pass


def test_reconciliation_reports_price_and_missing_sessions():
    first = bar("ALPHA", date(2026, 1, 2))
    second = first.model_copy(update={"close": first.close + 1})
    differences = reconcile([first], [second])
    assert [(item.field, item.primary, item.secondary) for item in differences] == [
        ("close", str(first.close), str(second.close))
    ]
    assert reconcile([first], [])[0].field == "session"


def test_structured_logging_redacts_secret_fields(caplog):
    import logging

    with caplog.at_level(logging.INFO):
        log_event(logging.getLogger("test"), "fetch", job_id="1", access_token="secret")
    assert "secret" not in caplog.text and "job_id" in caplog.text


def test_universe_is_explicitly_not_point_in_time_complete():
    assert not NIFTY200_V1.point_in_time_complete
    result = evaluate_eligibility(instrument(), [], unresolved_critical_incident=False)
    assert not result.eligible and "INSUFFICIENT_HISTORY" in result.reasons
