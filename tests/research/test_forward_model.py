from __future__ import annotations

from datetime import UTC, date, datetime

import numpy as np
import pytest
from research_core.forward_model import (
    BinaryCalibrator,
    ForwardModelError,
    FrozenForwardModelArtifact,
    FrozenHorizonModel,
)
from research_core.prediction_v1 import FEATURES
from sklearn.linear_model import LogisticRegression


def horizon(horizon_sessions: int = 1) -> FrozenHorizonModel:
    feature_count = len(FEATURES)
    return FrozenHorizonModel(
        horizon=horizon_sessions,
        model_name="logistic",
        imputer_statistics=(0.0,) * feature_count,
        indicator_features=(),
        scaler_mean=(0.0,) * feature_count,
        scaler_scale=(1.0,) * feature_count,
        coefficients=((0.0,) * feature_count,) * 3,
        intercepts=(-1.0, 0.0, 1.0),
        calibrators=(
            BinaryCalibrator(coefficient=1.0, intercept=0.0),
            BinaryCalibrator(coefficient=1.0, intercept=0.0),
            BinaryCalibrator(coefficient=1.0, intercept=0.0),
        ),
        ood_medians=(0.0,) * feature_count,
        ood_scales=(1.0,) * feature_count,
        train_rows=100,
        calibration_rows=30,
        train_end=date(2025, 12, 1),
        calibration_start=date(2025, 12, 2),
        calibration_end=date(2026, 9, 4),
    )


def artifact() -> FrozenForwardModelArtifact:
    return FrozenForwardModelArtifact(
        dataset_hash="a" * 64,
        registration_hash="b" * 64,
        pre_holdout_decision_hash="c" * 64,
        holdout_report_hash="d" * 64,
        feature_version="prediction-v1-causal-technical-1",
        target_version="prediction-v1-volatility-neutral-1",
        feature_names=FEATURES,
        training_cutoff=date(2026, 9, 4),
        source_manifest_created_at=datetime(2026, 9, 7, tzinfo=UTC),
        build_code_sha="1234567",
        abstention_policy={"minimum_top_probability": 0.45},
        ood_policy={"z_threshold": 4.0},
        models=(horizon(1), horizon(3), horizon(5), horizon(10)),
    )


def test_portable_model_is_sealed_and_probability_safe() -> None:
    model = horizon()
    values = model.probabilities({name: 0.0 for name in FEATURES})
    assert sum(values) == pytest.approx(1.0)
    assert values[2] > values[1] > values[0]
    assert model.ood_state({name: 0.0 for name in FEATURES}) == "IN_DISTRIBUTION"
    with pytest.raises(ForwardModelError, match="unknown frozen features"):
        model.probabilities({"future_return": 1.0})


def test_manual_binary_calibration_matches_sklearn_semantics() -> None:
    raw = np.array([[0.1], [0.3], [0.8], [0.9]])
    labels = np.array([0, 0, 1, 1])
    fitted = LogisticRegression(max_iter=300).fit(raw, labels)
    exported = BinaryCalibrator(
        coefficient=float(fitted.coef_[0, 0]), intercept=float(fitted.intercept_[0])
    )
    expected = fitted.predict_proba(raw)[:, 1]
    actual = 1 / (1 + np.exp(-(raw[:, 0] * exported.coefficient + exported.intercept)))
    assert actual == pytest.approx(expected)


def test_artifact_hash_detects_tampering_and_remains_disabled() -> None:
    model = artifact()
    assert len(model.artifact_hash) == 64
    assert model.public_delivery == "BLOCKED"
    assert model.forward_predictions_started is False
    changed = model.model_dump(mode="json")
    changed["dataset_hash"] = "e" * 64
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        FrozenForwardModelArtifact.model_validate(changed)
