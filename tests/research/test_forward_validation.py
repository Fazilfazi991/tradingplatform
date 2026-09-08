import math
import sqlite3
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from research_core.forward_runtime import (
    ForwardMarketObservation,
    ForwardPaperRuntime,
    ForwardRuntimeError,
    FrozenForwardPackage,
)
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
        "information_cutoff": NOW - timedelta(minutes=1),
        "market_data_cutoff": NOW - timedelta(minutes=2),
        "outcome_available_at": NOW + timedelta(days=1),
        "decision": ForwardDecision.ISSUED,
        "probabilities": (0.2, 0.5, 0.3),
        "baseline_probabilities": (0.33, 0.34, 0.33),
        "dataset_hash": HASH,
        "model_hash": "b" * 64,
        "feature_config_hash": "c" * 64,
        "feature_snapshot_hash": "d" * 64,
        "model_version": "forward-model-v1",
        "target_version": "prediction-v1-volatility-neutral-1",
        "ood_state": "IN_DISTRIBUTION",
        "market_regime": "NORMAL",
        "provenance": {"source": "UPSTOX_INTERNAL", "public_delivery": "BLOCKED"},
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
        ledger.resolve(
            outcome.model_copy(update={"outcome_id": uuid.uuid4()}),
            now=NOW + timedelta(days=1),
        )
    report = ledger.report()
    assert report["outcome_coverage"] == 1.0
    assert report["multiclass_brier"] == pytest.approx(0.78)
    assert report["log_loss"] == pytest.approx(-math.log(0.3))
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
        "abstention_rate": 0.0,
        "multiclass_brier": None,
        "log_loss": None,
        "calibration_error": None,
        "baseline_multiclass_brier": None,
        "baseline_log_loss": None,
        "brier_improvement_vs_baseline": None,
        "log_loss_improvement_vs_baseline": None,
        "by_horizon": {},
        "ood_counts": {
            "IN_DISTRIBUTION": 0,
            "WEAK_OOD": 0,
            "STRONG_OOD": 0,
            "UNKNOWN": 0,
        },
        "regime_counts": {},
        "metrics_state": "INSUFFICIENT_FORWARD_OUTCOMES",
        "ledger_hash": ledger.report()["ledger_hash"],
    }
    ledger.close()


def package(**updates) -> FrozenForwardPackage:
    values = {
        "approved": True,
        "dataset_hash": HASH,
        "model_hash": "b" * 64,
        "feature_config_hash": "c" * 64,
        "registration_hash": "d" * 64,
        "holdout_report_hash": "e" * 64,
        "horizons": (1, 3, 5, 10),
        "created_at": NOW,
        "code_sha": "315d043",
    }
    values.update(updates)
    return FrozenForwardPackage(**values)


def test_forward_runtime_requires_approved_frozen_package(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    with pytest.raises(ForwardRuntimeError, match="not approved"):
        ForwardPaperRuntime(ledger, package(approved=False))


def test_forward_runtime_rejects_package_drift_before_any_issue(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    runtime = ForwardPaperRuntime(ledger, package())
    with pytest.raises(ForwardRuntimeError, match="model hash"):
        runtime.issue_batch([prediction(model_hash="f" * 64)], now=NOW)
    assert ledger.report()["predictions_total"] == 0


def test_forward_issuance_batch_is_atomic_on_duplicate(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    runtime = ForwardPaperRuntime(ledger, package())
    first = prediction(symbol="RELIANCE")
    duplicate = prediction(symbol="RELIANCE")
    with pytest.raises(ForwardLedgerError, match="duplicate"):
        runtime.issue_batch([first, duplicate], now=NOW)
    assert ledger.report()["predictions_total"] == 0


def test_forward_runtime_derives_outcome_from_exact_session_window(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    runtime = ForwardPaperRuntime(ledger, package())
    item = prediction()
    assert runtime.issue_batch([item], now=NOW) == 1
    observation = ForwardMarketObservation(
        prediction_id=str(item.prediction_id),
        symbol="RELIANCE",
        session_dates=(date(2026, 9, 8), date(2026, 9, 9)),
        closes=(100.0, 101.0),
        neutral_threshold=0.005,
        observed_at=NOW + timedelta(days=1),
        source="UPSTOX_INTERNAL",
        source_payload_hash="f" * 64,
    )
    runtime.resolve_observation(observation, now=NOW + timedelta(days=1))
    outcome = ledger.outcomes()[0]
    assert outcome.realized_class == 2
    assert outcome.realized_return == pytest.approx(0.01)
    assert ledger.unresolved_issued() == []


def test_abstention_cannot_receive_an_outcome(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    item = prediction(
        decision=ForwardDecision.ABSTAINED,
        probabilities=None,
        abstention_reasons=("STRONG_OOD",),
    )
    ledger.issue(item, now=NOW)
    outcome = ForwardOutcome(
        prediction_id=item.prediction_id,
        resolved_at=NOW + timedelta(days=1),
        realized_class=1,
        realized_return=0.0,
        market_data_hash="f" * 64,
    )
    with pytest.raises(ForwardLedgerError, match="abstained"):
        ledger.resolve(outcome, now=NOW + timedelta(days=1))


def test_forward_contract_rejects_noncausal_cutoffs_and_bad_baseline():
    with pytest.raises(ValueError, match="cutoffs"):
        prediction(information_cutoff=NOW + timedelta(seconds=1))
    with pytest.raises(ValueError, match="baseline probabilities"):
        prediction(baseline_probabilities=(0.2, 0.2, 0.2))


def test_forward_report_preserves_baseline_and_cohort_evidence(tmp_path):
    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    item = prediction()
    ledger.issue(item, now=NOW)
    ledger.resolve(
        ForwardOutcome(
            prediction_id=item.prediction_id,
            resolved_at=NOW + timedelta(days=1),
            realized_class=2,
            realized_return=0.01,
            market_data_hash="f" * 64,
        ),
        now=NOW + timedelta(days=1),
    )
    report = ledger.report()
    assert report["baseline_multiclass_brier"] == pytest.approx(0.6734)
    assert report["brier_improvement_vs_baseline"] == pytest.approx(0.6734 - 0.78)
    assert report["by_horizon"]["1"]["resolved"] == 1
    assert report["ood_counts"]["IN_DISTRIBUTION"] == 1
    assert report["regime_counts"] == {"NORMAL": 1}
    ledger.close()
