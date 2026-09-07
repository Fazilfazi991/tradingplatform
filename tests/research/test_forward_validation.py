import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest
from research_core.forward_validation import (
    ForwardDecision,
    ForwardLedgerError,
    ForwardOutcome,
    ForwardPrediction,
    ForwardValidationLedger,
)

NOW = datetime(2026, 9, 8, 12, tzinfo=UTC)
HASH = "a" * 64


def prediction(**updates) -> ForwardPrediction:
    values = {
        "symbol": "RELIANCE",
        "as_of_date": date(2026, 9, 8),
        "horizon_sessions": 1,
        "issued_at": NOW,
        "outcome_available_at": NOW + timedelta(days=1),
        "decision": ForwardDecision.ISSUED,
        "probabilities": (0.2, 0.5, 0.3),
        "dataset_hash": HASH,
        "model_hash": "b" * 64,
        "feature_config_hash": "c" * 64,
        "code_sha": "315d043",
    }
    values.update(updates)
    return ForwardPrediction(**values)


def test_forward_ledger_is_causal_unique_and_append_only(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    item = prediction()
    ledger.issue(item, now=NOW)
    with pytest.raises(ForwardLedgerError, match="duplicate"):
        ledger.issue(prediction(), now=NOW)
    outcome = ForwardOutcome(
        prediction_id=item.prediction_id,
        resolved_at=NOW + timedelta(days=1),
        realized_class=2,
        realized_return=0.012,
        market_data_hash="d" * 64,
    )
    with pytest.raises(ForwardLedgerError, match="causally"):
        ledger.resolve(outcome, now=NOW)
    ledger.resolve(outcome, now=NOW + timedelta(days=1))
    with pytest.raises(ForwardLedgerError, match="already resolved"):
        ledger.resolve(outcome.model_copy(update={"outcome_id": __import__("uuid").uuid4()}), now=NOW + timedelta(days=1))
    assert ledger.report()["outcome_coverage"] == 1.0
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        ledger.connection.execute("UPDATE forward_predictions SET issued_at='x'")
    ledger.close()


def test_abstention_cannot_smuggle_probabilities():
    with pytest.raises(ValueError, match="abstentions"):
        prediction(
            decision=ForwardDecision.ABSTAINED,
            abstention_reasons=("STRONG_OOD",),
        )


def test_empty_ledger_truthfully_remains_forward_required(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    assert ledger.report() == {
        "status": "FORWARD REQUIRED",
        "research_mode": "ENGINEERING_FIXTURE",
        "public_delivery": "BLOCKED",
        "predictions_total": 0,
        "issued": 0,
        "abstained": 0,
        "outcomes_resolved": 0,
        "outcome_coverage": 0.0,
        "ledger_hash": ledger.report()["ledger_hash"],
    }
    ledger.close()
