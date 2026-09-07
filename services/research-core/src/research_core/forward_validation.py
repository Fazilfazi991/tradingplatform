from __future__ import annotations

import math
import sqlite3
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_core.common import stable_hash


class ForwardLedgerError(ValueError):
    pass


class ForwardDecision(StrEnum):
    ISSUED = "ISSUED"
    ABSTAINED = "ABSTAINED"


class ForwardPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    prediction_id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(min_length=1, max_length=40)
    as_of_date: date
    horizon_sessions: int = Field(gt=0)
    issued_at: datetime
    outcome_available_at: datetime
    decision: ForwardDecision
    probabilities: tuple[float, float, float] | None = None
    abstention_reasons: tuple[str, ...] = ()
    dataset_hash: str = Field(min_length=64, max_length=64)
    model_hash: str = Field(min_length=64, max_length=64)
    feature_config_hash: str = Field(min_length=64, max_length=64)
    code_sha: str = Field(min_length=7, max_length=64)
    research_mode: Literal["ENGINEERING_FIXTURE"] = "ENGINEERING_FIXTURE"
    public_delivery: Literal["BLOCKED"] = "BLOCKED"
    record_hash: str = ""

    @model_validator(mode="after")
    def validate_causal_record(self) -> ForwardPrediction:
        if self.outcome_available_at <= self.issued_at:
            raise ValueError("outcome must become available after issuance")
        if self.decision is ForwardDecision.ISSUED:
            if self.probabilities is None or self.abstention_reasons:
                raise ValueError("issued predictions require probabilities and no abstention reasons")
            if any(value < 0 or value > 1 for value in self.probabilities):
                raise ValueError("probabilities must be in [0,1]")
            if abs(sum(self.probabilities) - 1.0) > 1e-6:
                raise ValueError("probabilities must sum to one")
        elif self.probabilities is not None or not self.abstention_reasons:
            raise ValueError("abstentions require reasons and cannot carry probabilities")
        expected = stable_hash(self.model_dump(exclude={"record_hash"}, mode="json"))
        if self.record_hash and self.record_hash != expected:
            raise ValueError("prediction record hash mismatch")
        if not self.record_hash:
            object.__setattr__(self, "record_hash", expected)
        return self


class ForwardOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome_id: UUID = Field(default_factory=uuid4)
    prediction_id: UUID
    resolved_at: datetime
    realized_class: Literal[0, 1, 2]
    realized_return: float
    market_data_hash: str = Field(min_length=64, max_length=64)
    record_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> ForwardOutcome:
        expected = stable_hash(self.model_dump(exclude={"record_hash"}, mode="json"))
        if self.record_hash and self.record_hash != expected:
            raise ValueError("outcome record hash mismatch")
        if not self.record_hash:
            object.__setattr__(self, "record_hash", expected)
        return self


class ForwardValidationLedger:
    """Append-only internal paper ledger; it never emits public predictions."""

    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(Path(path))
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS forward_predictions (
          prediction_id TEXT PRIMARY KEY, uniqueness_key TEXT UNIQUE NOT NULL,
          issued_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS forward_outcomes (
          outcome_id TEXT PRIMARY KEY, prediction_id TEXT UNIQUE NOT NULL,
          resolved_at TEXT NOT NULL, payload_json TEXT NOT NULL,
          FOREIGN KEY(prediction_id) REFERENCES forward_predictions(prediction_id)
        );
        CREATE TRIGGER IF NOT EXISTS forward_predictions_no_update
          BEFORE UPDATE ON forward_predictions BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS forward_predictions_no_delete
          BEFORE DELETE ON forward_predictions BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS forward_outcomes_no_update
          BEFORE UPDATE ON forward_outcomes BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS forward_outcomes_no_delete
          BEFORE DELETE ON forward_outcomes BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        """)
        self.connection.commit()

    def issue(self, prediction: ForwardPrediction, *, now: datetime) -> None:
        self.issue_batch([prediction], now=now)

    def issue_batch(self, predictions: list[ForwardPrediction], *, now: datetime) -> None:
        if not predictions:
            raise ForwardLedgerError("empty forward prediction batch")
        observed = now.astimezone(UTC)
        if any(prediction.issued_at > observed for prediction in predictions):
            raise ForwardLedgerError("prediction cannot be issued in the future")
        rows = []
        for prediction in predictions:
            key = stable_hash(
                {
                    "symbol": prediction.symbol,
                    "as_of_date": prediction.as_of_date,
                    "horizon_sessions": prediction.horizon_sessions,
                    "model_hash": prediction.model_hash,
                }
            )
            rows.append(
                (
                    str(prediction.prediction_id),
                    key,
                    prediction.issued_at.astimezone(UTC).isoformat(),
                    prediction.model_dump_json(),
                )
            )
        try:
            self.connection.executemany(
                "INSERT INTO forward_predictions VALUES(?,?,?,?)", rows
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise ForwardLedgerError("duplicate forward prediction") from error

    def resolve(self, outcome: ForwardOutcome, *, now: datetime) -> None:
        row = self.connection.execute(
            "SELECT payload_json FROM forward_predictions WHERE prediction_id=?",
            (str(outcome.prediction_id),),
        ).fetchone()
        if not row:
            raise ForwardLedgerError("prediction does not exist")
        prediction = ForwardPrediction.model_validate_json(row[0])
        if prediction.decision is ForwardDecision.ABSTAINED:
            raise ForwardLedgerError("abstained predictions cannot receive outcomes")
        observed = now.astimezone(UTC)
        if observed < prediction.outcome_available_at or outcome.resolved_at < prediction.outcome_available_at:
            raise ForwardLedgerError("outcome is not yet causally available")
        if outcome.resolved_at > observed:
            raise ForwardLedgerError("outcome cannot be resolved in the future")
        try:
            self.connection.execute(
                "INSERT INTO forward_outcomes VALUES(?,?,?,?)",
                (
                    str(outcome.outcome_id),
                    str(outcome.prediction_id),
                    outcome.resolved_at.astimezone(UTC).isoformat(),
                    outcome.model_dump_json(),
                ),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise ForwardLedgerError("prediction outcome already resolved") from error

    def report(self) -> dict[str, Any]:
        predictions = self.predictions()
        outcomes = self.outcomes()
        issued = sum(item.decision is ForwardDecision.ISSUED for item in predictions)
        by_prediction = {item.prediction_id: item for item in outcomes}
        scored = [
            (prediction, by_prediction[prediction.prediction_id])
            for prediction in predictions
            if prediction.decision is ForwardDecision.ISSUED
            and prediction.prediction_id in by_prediction
        ]
        brier = None
        log_loss = None
        if scored:
            brier_values = []
            log_losses = []
            for prediction, outcome in scored:
                assert prediction.probabilities is not None
                truth = tuple(float(index == outcome.realized_class) for index in range(3))
                brier_values.append(
                    sum((probability - actual) ** 2 for probability, actual in zip(prediction.probabilities, truth))
                )
                log_losses.append(-math.log(max(prediction.probabilities[outcome.realized_class], 1e-15)))
            brier = sum(brier_values) / len(brier_values)
            log_loss = sum(log_losses) / len(log_losses)
        return {
            "status": "FORWARD VALIDATION IN PROGRESS" if predictions else "FORWARD REQUIRED",
            "research_mode": "ENGINEERING_FIXTURE",
            "public_delivery": "BLOCKED",
            "predictions_total": len(predictions),
            "issued": issued,
            "abstained": len(predictions) - issued,
            "outcomes_resolved": len(outcomes),
            "outcome_coverage": len(outcomes) / issued if issued else 0.0,
            "abstention_rate": (len(predictions) - issued) / len(predictions) if predictions else 0.0,
            "multiclass_brier": brier,
            "log_loss": log_loss,
            "metrics_state": "AVAILABLE" if scored else "INSUFFICIENT_FORWARD_OUTCOMES",
            "ledger_hash": stable_hash(
                {
                    "predictions": [item.record_hash for item in predictions],
                    "outcomes": [item.record_hash for item in outcomes],
                }
            ),
        }

    def predictions(self) -> list[ForwardPrediction]:
        return [
            ForwardPrediction.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM forward_predictions ORDER BY issued_at,prediction_id"
            )
        ]

    def outcomes(self) -> list[ForwardOutcome]:
        return [
            ForwardOutcome.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM forward_outcomes ORDER BY resolved_at,outcome_id"
            )
        ]

    def unresolved_issued(self) -> list[ForwardPrediction]:
        return [
            ForwardPrediction.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT p.payload_json FROM forward_predictions p "
                "LEFT JOIN forward_outcomes o ON o.prediction_id=p.prediction_id "
                "WHERE o.prediction_id IS NULL ORDER BY p.issued_at,p.prediction_id"
            )
            if ForwardPrediction.model_validate_json(row[0]).decision is ForwardDecision.ISSUED
        ]

    def close(self) -> None:
        self.connection.close()
