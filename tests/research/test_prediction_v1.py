from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from research_core.objects import PredictionResearchOutput, PredictionTargetVersion
from research_core.prediction_v1 import (
    DatasetFreezeError,
    HoldoutAccessError,
    V1Paths,
    apply_calibrators,
    build_registration,
    build_v1_frame,
    fit_calibrators,
    public_prediction_guard,
    require_pre_holdout,
    structural_action_exclusions,
    verify_frozen_dataset,
    write_registration,
)

from scripts.finalize_prediction_v1_report import audit_decision


def manifest() -> dict:
    return {
        "dataset_hash": "7ce7f964ca6aa8b551c68749e5f2d8a5a95e5e6c7b08005350807431fd866e6b",
        "universe_snapshot_hash": "u",
        "instrument_count": 200,
        "bar_count": 442_837,
    }


def test_registration_is_sealed_and_immutable(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    dataset.mkdir()
    (dataset / "dataset-manifest.json").write_text(json.dumps(manifest()))
    paths = V1Paths(dataset, tmp_path / "out")
    registration = build_registration(manifest=verify_frozen_dataset(paths), code_sha="abc")
    write_registration(paths, registration)
    changed = {**registration, "registration_hash": "different"}
    with pytest.raises(DatasetFreezeError):
        write_registration(paths, changed)


def test_dataset_freeze_fails_closed(tmp_path: Path) -> None:
    tmp_path.joinpath("dataset-manifest.json").write_text(
        json.dumps({**manifest(), "dataset_hash": "bad"})
    )
    with pytest.raises(DatasetFreezeError):
        verify_frozen_dataset(V1Paths(tmp_path, tmp_path / "out"))


def test_volatility_neutral_target_and_latest_labels() -> None:
    dates = pd.date_range("2020-01-01", periods=300, tz="UTC")
    close = np.linspace(100, 130, 300)
    bars = pd.DataFrame(
        {
            "instrument_id": "a",
            "symbol": "A",
            "session_date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": np.arange(300) + 100,
        }
    )
    frame = build_v1_frame(bars, pd.Series(False, index=bars.index))
    assert pd.isna(frame.iloc[-1]["target_direction_1"])
    assert pd.isna(frame.iloc[-10]["target_direction_10"])
    assert frame.iloc[260]["history_count"] == 261


def test_structural_actions_are_excluded_but_dividends_are_not(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    dataset.mkdir()
    dataset.joinpath("corporate-actions.json").write_text(
        json.dumps(
            {
                "A": [
                    {"action_type": "SPLIT", "effective_date": "2024-02-01"},
                    {"action_type": "DIVIDEND", "effective_date": "2024-03-01"},
                ]
            }
        )
    )
    bars = pd.DataFrame(
        {"symbol": "A", "session_date": pd.date_range("2024-01-01", periods=80, tz="UTC")}
    )
    excluded, report = structural_action_exclusions(V1Paths(dataset, tmp_path), bars)
    assert report["structural_actions"] == 1
    assert 1 <= excluded.sum() <= 41


def test_calibration_is_fit_on_explicit_calibration_data() -> None:
    raw = np.array(
        [
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
            [0.7, 0.2, 0.1],
            [0.2, 0.7, 0.1],
            [0.2, 0.1, 0.7],
        ]
    )
    y = np.array([0, 1, 2, 0, 1, 2])
    calibrated = apply_calibrators(fit_calibrators(raw, y), raw)
    assert np.allclose(calibrated.sum(axis=1), 1)


def test_holdout_gate_and_public_guard(tmp_path: Path) -> None:
    path = tmp_path / "pre.json"
    with pytest.raises(HoldoutAccessError):
        require_pre_holdout(path, "r")
    path.write_text(json.dumps({"registration_hash": "r", "sealed": True}))
    assert require_pre_holdout(path, "r")["sealed"]
    with pytest.raises(PermissionError):
        public_prediction_guard(destination="PUBLIC_WEB")
    public_prediction_guard(destination="INTERNAL_RESEARCH")


def test_prediction_contract_and_target_version() -> None:
    target = PredictionTargetVersion(
        version="v1",
        horizon=5,
        neutral_band_methodology="past-only-volatility",
        barrier_definitions={"up": 0.02},
        volatility_target_methodology="future-path-realized",
        mfe_mae_methodology="future-extrema",
    )
    assert target.definition_hash
    output = PredictionResearchOutput(
        entity="RELIANCE",
        cutoff=datetime.now(UTC),
        horizon=5,
        dataset_id="d",
        feature_version="f",
        model_version="m",
        target_version="t",
        research_status="INCONCLUSIVE",
        prob_up=0.3,
        prob_neutral=0.4,
        prob_down=0.3,
        calibration_status="CALIBRATED",
        ood_state="IN_DISTRIBUTION",
        abstention=True,
        data_quality="PASS",
        provenance={"mode": "INTERNAL"},
    )
    assert output.payload_hash


def test_holdout_audit_uses_all_preregistered_dimensions() -> None:
    registration = {
        "holdout_pass_criteria": {
            "brier_improvement_vs_unconditional": 0.002,
            "log_loss_improvement_vs_unconditional": 0.002,
            "ece_max": 0.08,
            "positive_validation_folds_fraction_min": 0.6,
        }
    }
    walk = {"aggregates": [{"horizon": 5, "model": "logistic", "positive_brier_folds": 2}]}
    holdout = {
        "results": [
            {
                "horizon": 5,
                "model": "logistic",
                "brier_improvement": 0.003,
                "baseline": {"log_loss": 1.01},
                "metrics": {"log_loss": 1.0, "ece": 0.03},
                "abstention": {"coverage": 0.2},
            }
        ]
    }
    assert audit_decision(registration, walk, holdout)["all_preregistered_criteria_pass"]
    holdout["results"][0]["metrics"]["ece"] = 0.2
    assert not audit_decision(registration, walk, holdout)["all_preregistered_criteria_pass"]
