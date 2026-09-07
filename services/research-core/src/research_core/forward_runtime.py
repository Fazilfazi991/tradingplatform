from __future__ import annotations

import math
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_core.common import stable_hash
from research_core.forward_validation import (
    ForwardLedgerError,
    ForwardOutcome,
    ForwardPrediction,
    ForwardValidationLedger,
)


class ForwardRuntimeError(ValueError):
    pass


class FrozenForwardPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["forward-package-v1"] = "forward-package-v1"
    approved: bool = False
    dataset_hash: str = Field(min_length=64, max_length=64)
    model_hash: str = Field(min_length=64, max_length=64)
    feature_config_hash: str = Field(min_length=64, max_length=64)
    registration_hash: str = Field(min_length=64, max_length=64)
    holdout_report_hash: str = Field(min_length=64, max_length=64)
    horizons: tuple[int, ...]
    created_at: datetime
    code_sha: str = Field(min_length=7, max_length=64)
    public_delivery: Literal["BLOCKED"] = "BLOCKED"
    package_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> FrozenForwardPackage:
        if not self.horizons or any(item <= 0 for item in self.horizons):
            raise ValueError("package requires positive horizons")
        if len(set(self.horizons)) != len(self.horizons):
            raise ValueError("package horizons must be unique")
        expected = stable_hash(self.model_dump(exclude={"package_hash"}, mode="json"))
        if self.package_hash and self.package_hash != expected:
            raise ValueError("forward package hash mismatch")
        if not self.package_hash:
            object.__setattr__(self, "package_hash", expected)
        return self


class ForwardMarketObservation(BaseModel):
    """Bounded evidence for one completed trading-session horizon."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    prediction_id: str
    symbol: str
    session_dates: tuple[date, ...]
    closes: tuple[float, ...]
    neutral_threshold: float = Field(ge=0)
    observed_at: datetime
    source: str = Field(min_length=1, max_length=80)
    source_payload_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_series(self) -> ForwardMarketObservation:
        if len(self.session_dates) != len(self.closes) or len(self.closes) < 2:
            raise ValueError("session dates and closes must describe a completed window")
        if tuple(sorted(set(self.session_dates))) != self.session_dates:
            raise ValueError("session dates must be unique and increasing")
        if any(not math.isfinite(value) or value <= 0 for value in self.closes):
            raise ValueError("closes must be finite and positive")
        return self


class ForwardPaperRuntime:
    """Internal causal issuer/resolver. It cannot make or publish model predictions."""

    def __init__(self, ledger: ForwardValidationLedger, package: FrozenForwardPackage) -> None:
        if not package.approved:
            raise ForwardRuntimeError("forward package is not approved")
        self.ledger = ledger
        self.package = package

    @classmethod
    def from_package_file(
        cls, ledger: ForwardValidationLedger, path: str | Path
    ) -> ForwardPaperRuntime:
        package = FrozenForwardPackage.model_validate_json(Path(path).read_text(encoding="utf-8"))
        return cls(ledger, package)

    def issue_batch(self, predictions: list[ForwardPrediction], *, now: datetime) -> int:
        if not predictions:
            raise ForwardRuntimeError("empty issuance batch")
        for prediction in predictions:
            if prediction.dataset_hash != self.package.dataset_hash:
                raise ForwardRuntimeError("prediction dataset hash differs from frozen package")
            if prediction.model_hash != self.package.model_hash:
                raise ForwardRuntimeError("prediction model hash differs from frozen package")
            if prediction.feature_config_hash != self.package.feature_config_hash:
                raise ForwardRuntimeError("prediction feature hash differs from frozen package")
            if prediction.horizon_sessions not in self.package.horizons:
                raise ForwardRuntimeError("prediction horizon is not approved")
            if prediction.code_sha != self.package.code_sha:
                raise ForwardRuntimeError("prediction code SHA differs from frozen package")
        self.ledger.issue_batch(predictions, now=now)
        return len(predictions)

    def resolve_observation(self, observation: ForwardMarketObservation, *, now: datetime) -> None:
        try:
            prediction = next(
                item
                for item in self.ledger.unresolved_issued()
                if str(item.prediction_id) == observation.prediction_id
            )
        except StopIteration as error:
            raise ForwardRuntimeError("no unresolved issued prediction matches observation") from error
        if prediction.symbol != observation.symbol:
            raise ForwardRuntimeError("observation symbol mismatch")
        if observation.session_dates[0] != prediction.as_of_date:
            raise ForwardRuntimeError("observation does not start at prediction cutoff")
        if len(observation.session_dates) != prediction.horizon_sessions + 1:
            raise ForwardRuntimeError("observation session count does not match horizon")
        if observation.observed_at > now.astimezone(UTC):
            raise ForwardRuntimeError("observation cannot be from the future")
        realized_return = observation.closes[-1] / observation.closes[0] - 1
        realized_class: Literal[0, 1, 2] = (
            2
            if realized_return > observation.neutral_threshold
            else 0
            if realized_return < -observation.neutral_threshold
            else 1
        )
        outcome = ForwardOutcome(
            prediction_id=prediction.prediction_id,
            resolved_at=observation.observed_at,
            realized_class=realized_class,
            realized_return=realized_return,
            market_data_hash=stable_hash(observation.model_dump(mode="json")),
        )
        try:
            self.ledger.resolve(outcome, now=now)
        except ForwardLedgerError as error:
            raise ForwardRuntimeError(str(error)) from error
