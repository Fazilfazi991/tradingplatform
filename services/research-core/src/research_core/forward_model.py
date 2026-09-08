from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from research_core.common import stable_hash
from research_core.prediction_v1 import FEATURES, apply_calibrators, fit_calibrators, model_pipeline


class ForwardModelError(ValueError):
    pass


def _feature_value(features: dict[str, float | None], name: str) -> float:
    value = features.get(name)
    return np.nan if value is None else float(value)


class BinaryCalibrator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    coefficient: float
    intercept: float


class FrozenHorizonModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    horizon: int = Field(gt=0)
    model_name: Literal["logistic", "regularized_logistic"]
    classes: tuple[int, int, int] = (0, 1, 2)
    imputer_statistics: tuple[float, ...]
    indicator_features: tuple[int, ...]
    scaler_mean: tuple[float, ...]
    scaler_scale: tuple[float, ...]
    coefficients: tuple[tuple[float, ...], ...]
    intercepts: tuple[float, float, float]
    calibrators: tuple[BinaryCalibrator, BinaryCalibrator, BinaryCalibrator]
    ood_medians: tuple[float, ...]
    ood_scales: tuple[float, ...]
    train_rows: int = Field(gt=0)
    calibration_rows: int = Field(gt=0)
    train_end: date
    calibration_start: date
    calibration_end: date

    @model_validator(mode="after")
    def dimensions_match(self) -> FrozenHorizonModel:
        feature_count = len(FEATURES)
        transformed = feature_count + len(self.indicator_features)
        if len(self.imputer_statistics) != feature_count:
            raise ValueError("imputer statistics do not match the frozen feature set")
        if any(index < 0 or index >= feature_count for index in self.indicator_features):
            raise ValueError("indicator feature index is invalid")
        if len(self.scaler_mean) != transformed or len(self.scaler_scale) != transformed:
            raise ValueError("scaler dimensions do not match transformed features")
        if len(self.coefficients) != 3 or any(
            len(row) != transformed for row in self.coefficients
        ):
            raise ValueError("coefficient dimensions do not match transformed features")
        if len(self.ood_medians) != feature_count or len(self.ood_scales) != feature_count:
            raise ValueError("OOD dimensions do not match the frozen feature set")
        if any(not math.isfinite(value) or value <= 0 for value in self.scaler_scale):
            raise ValueError("scaler scale must be finite and positive")
        if any(not math.isfinite(value) or value <= 0 for value in self.ood_scales):
            raise ValueError("OOD scale must be finite and positive")
        if not self.train_end < self.calibration_start <= self.calibration_end:
            raise ValueError("training and calibration partitions must be chronological")
        return self

    def probabilities(self, features: dict[str, float | None]) -> tuple[float, float, float]:
        unknown = set(features) - set(FEATURES)
        if unknown:
            raise ForwardModelError(f"unknown frozen features: {sorted(unknown)}")
        raw = np.array(
            [_feature_value(features, name) for name in FEATURES],
            dtype=float,
        )
        raw[~np.isfinite(raw)] = np.nan
        missing = np.isnan(raw)
        transformed = np.where(missing, np.asarray(self.imputer_statistics), raw)
        if self.indicator_features:
            transformed = np.concatenate(
                [transformed, missing[np.asarray(self.indicator_features)].astype(float)]
            )
        scaled = (transformed - np.asarray(self.scaler_mean)) / np.asarray(self.scaler_scale)
        logits = np.asarray(self.coefficients) @ scaled + np.asarray(self.intercepts)
        logits -= logits.max()
        uncalibrated = np.exp(logits)
        uncalibrated /= uncalibrated.sum()
        calibrated = np.array(
            [
                1.0
                / (1.0 + math.exp(-(item.coefficient * uncalibrated[index] + item.intercept)))
                for index, item in enumerate(self.calibrators)
            ]
        )
        calibrated /= calibrated.sum()
        return tuple(float(value) for value in calibrated)  # type: ignore[return-value]

    def ood_state(self, features: dict[str, float | None]) -> str:
        raw = np.array(
            [_feature_value(features, name) for name in FEATURES],
            dtype=float,
        )
        raw[~np.isfinite(raw)] = np.nan
        values = np.where(np.isnan(raw), np.asarray(self.ood_medians), raw)
        extreme = int(
            np.sum(
                np.abs(values - np.asarray(self.ood_medians)) / np.asarray(self.ood_scales) > 4.0
            )
        )
        return "STRONG_OOD" if extreme >= 4 else "WEAK_OOD" if extreme >= 2 else "IN_DISTRIBUTION"


class FrozenForwardModelArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["forward-model-artifact-v1"] = "forward-model-artifact-v1"
    dataset_hash: str = Field(min_length=64, max_length=64)
    registration_hash: str = Field(min_length=64, max_length=64)
    pre_holdout_decision_hash: str = Field(min_length=64, max_length=64)
    holdout_report_hash: str = Field(min_length=64, max_length=64)
    feature_version: str
    target_version: str
    feature_names: tuple[str, ...]
    training_cutoff: date
    source_manifest_created_at: datetime
    build_code_sha: str = Field(min_length=7, max_length=64)
    refit_policy: Literal["POST_HOLDOUT_REFIT_WITH_FROZEN_SELECTION"] = (
        "POST_HOLDOUT_REFIT_WITH_FROZEN_SELECTION"
    )
    calibration_sessions: int = 126
    abstention_policy: dict[str, Any]
    ood_policy: dict[str, Any]
    models: tuple[FrozenHorizonModel, ...]
    public_delivery: Literal["BLOCKED"] = "BLOCKED"
    forward_predictions_started: Literal[False] = False
    artifact_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> FrozenForwardModelArtifact:
        if self.feature_names != FEATURES:
            raise ValueError("artifact feature order differs from Prediction V1")
        horizons = tuple(item.horizon for item in self.models)
        if horizons != (1, 3, 5, 10):
            raise ValueError("artifact must contain the four frozen horizons in order")
        expected = stable_hash(self.model_dump(exclude={"artifact_hash"}, mode="json"))
        if self.artifact_hash and self.artifact_hash != expected:
            raise ValueError("forward model artifact hash mismatch")
        if not self.artifact_hash:
            object.__setattr__(self, "artifact_hash", expected)
        return self

    @property
    def feature_config_hash(self) -> str:
        return stable_hash(
            {
                "feature_version": self.feature_version,
                "feature_names": self.feature_names,
                "abstention_policy": self.abstention_policy,
                "ood_policy": self.ood_policy,
            }
        )


def _extract_model(
    *,
    horizon: int,
    name: str,
    pipeline: Pipeline,
    calibrators: list[LogisticRegression],
    train: pd.DataFrame,
    calibration: pd.DataFrame,
) -> FrozenHorizonModel:
    imputer = pipeline.named_steps["imputer"]
    scaler = pipeline.named_steps["scale"]
    estimator = pipeline.named_steps["model"]
    if not isinstance(imputer, SimpleImputer) or not isinstance(scaler, StandardScaler):
        raise ForwardModelError("unexpected preprocessing pipeline")
    if not isinstance(estimator, LogisticRegression):
        raise ForwardModelError("only selected logistic models are eligible for V1 forward export")
    indicator = tuple(int(item) for item in imputer.indicator_.features_)
    raw_train = train[list(FEATURES)].replace([np.inf, -np.inf], np.nan)
    medians = raw_train.median().fillna(0.0).to_numpy(dtype=float)
    scales = raw_train.std().replace(0, np.nan).fillna(1.0).to_numpy(dtype=float)
    if name not in {"logistic", "regularized_logistic"}:
        raise ForwardModelError(f"unsupported selected model: {name}")
    exported_calibrators = [
        BinaryCalibrator(
            coefficient=float(calibrator.coef_[0, 0]),
            intercept=float(calibrator.intercept_[0]),
        )
        for calibrator in calibrators
    ]
    intercepts = [float(item) for item in estimator.intercept_]
    if len(intercepts) != 3 or len(exported_calibrators) != 3:
        raise ForwardModelError("forward classifier must expose exactly three classes")
    return FrozenHorizonModel(
        horizon=horizon,
        model_name=cast(Literal["logistic", "regularized_logistic"], name),
        imputer_statistics=tuple(float(item) for item in imputer.statistics_),
        indicator_features=indicator,
        scaler_mean=tuple(float(item) for item in scaler.mean_),
        scaler_scale=tuple(float(item) for item in scaler.scale_),
        coefficients=tuple(tuple(float(value) for value in row) for row in estimator.coef_),
        intercepts=(intercepts[0], intercepts[1], intercepts[2]),
        calibrators=(
            exported_calibrators[0],
            exported_calibrators[1],
            exported_calibrators[2],
        ),
        ood_medians=tuple(float(item) for item in medians),
        ood_scales=tuple(float(item) for item in scales),
        train_rows=len(train),
        calibration_rows=len(calibration),
        train_end=train.session_date.max().date(),
        calibration_start=calibration.session_date.min().date(),
        calibration_end=calibration.session_date.max().date(),
    )


def fit_frozen_forward_model(
    frame: pd.DataFrame,
    *,
    dataset_hash: str,
    registration: dict[str, Any],
    decision: dict[str, Any],
    holdout_report: dict[str, Any],
    source_manifest_created_at: datetime,
    code_sha: str,
) -> FrozenForwardModelArtifact:
    if holdout_report.get("holdout_access_count") != 1 or holdout_report.get("decision") != "HOLDOUT_PASS":
        raise ForwardModelError("a single passing sealed holdout is required")
    if holdout_report.get("forward_predictions_started") is not False:
        raise ForwardModelError("forward predictions have already started")
    if decision.get("registration_hash") != registration.get("registration_hash"):
        raise ForwardModelError("pre-holdout decision does not match registration")
    if holdout_report.get("pre_holdout_decision_hash") != decision.get("decision_hash"):
        raise ForwardModelError("holdout report does not match pre-holdout decision")

    models: list[FrozenHorizonModel] = []
    for selected in decision["selected_candidates"]:
        horizon = int(selected["horizon"])
        name = str(selected["model"])
        target = f"target_direction_{horizon}"
        eligible = (
            frame[(frame.history_count >= registration["minimum_history_sessions"])
                  & ~frame.corporate_action_excluded]
            .dropna(subset=[*FEATURES, target])
            .copy()
        )
        dates = sorted(eligible.session_date.unique())
        if len(dates) <= 126 + horizon:
            raise ForwardModelError(f"{horizon}D has insufficient refit history")
        calibration_dates = set(dates[-126:])
        purge_dates = set(dates[-(126 + horizon):-126])
        calibration = eligible[eligible.session_date.isin(calibration_dates)]
        train = eligible[
            (eligible.session_date < min(calibration_dates))
            & ~eligible.session_date.isin(purge_dates)
        ]
        pipeline = model_pipeline(name).fit(train[list(FEATURES)], train[target].astype(int))
        raw_calibration = pipeline.predict_proba(calibration[list(FEATURES)])
        calibrators = fit_calibrators(
            raw_calibration, calibration[target].astype(int).to_numpy()
        )
        exported = _extract_model(
            horizon=horizon,
            name=name,
            pipeline=pipeline,
            calibrators=calibrators,
            train=train,
            calibration=calibration,
        )
        sample = calibration[list(FEATURES)].iloc[: min(256, len(calibration))]
        expected = apply_calibrators(calibrators, pipeline.predict_proba(sample))
        actual = np.asarray(
            [exported.probabilities(row) for row in sample.to_dict(orient="records")]
        )
        if not np.allclose(expected, actual, atol=1e-12, rtol=1e-12):
            raise ForwardModelError(f"{horizon}D portable inference parity failed")
        models.append(exported)

    return FrozenForwardModelArtifact(
        dataset_hash=dataset_hash,
        registration_hash=registration["registration_hash"],
        pre_holdout_decision_hash=decision["decision_hash"],
        holdout_report_hash=stable_hash(holdout_report),
        feature_version=registration["feature_version"],
        target_version=registration["target_version"],
        feature_names=FEATURES,
        training_cutoff=date.fromisoformat(holdout_report["holdout"][1]),
        source_manifest_created_at=source_manifest_created_at,
        build_code_sha=code_sha,
        abstention_policy=registration["abstention_policy"],
        ood_policy=registration["ood_policy"],
        models=tuple(models),
    )
