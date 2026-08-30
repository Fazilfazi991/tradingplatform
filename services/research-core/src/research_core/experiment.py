from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import joblib

from research_core.calibration import ProbabilityCalibrator, calibration_curve_data
from research_core.common import file_hash, stable_hash
from research_core.features import build_feature_matrix
from research_core.fixtures import synthetic_market_fixture
from research_core.metrics import bootstrap_interval, classification_metrics
from research_core.models import UnconditionalClassifier, linear_explanation, model_pipeline
from research_core.objects import PredictionExperiment, ResearchMode
from research_core.policy import ResearchGatePolicy
from research_core.registry import ExperimentRegistry
from research_core.targets import build_targets


def run_synthetic_experiment(
    *,
    planted_edge: bool,
    output_root: str | Path,
    code_sha: str,
    seed: int = 17,
    register: bool = True,
) -> dict:
    ResearchGatePolicy.current().authorize(ResearchMode.ENGINEERING_FIXTURE)
    started = time.perf_counter()
    bars = synthetic_market_fixture(seed=seed, planted_edge=planted_edge)
    feature_start = time.perf_counter()
    features = build_feature_matrix(bars)
    feature_seconds = time.perf_counter() - feature_start
    target_start = time.perf_counter()
    targets = build_targets(bars)
    target_seconds = time.perf_counter() - target_start
    joined = features.values.join(targets.values, how="inner").reset_index()
    columns = [
        "return_1",
        "return_5",
        "return_20",
        "sma_distance_pct_20",
        "rsi_14",
        "atr_price_14",
        "volume_median_ratio_20",
        "drawdown_60",
    ]
    target = "target_direction_5"
    joined = joined.dropna(subset=[*columns, target]).copy()
    joined[target] = (joined[target] > 0).astype(int)
    dates = sorted(joined["session_date"].unique())
    train_end, calibration_end = dates[int(len(dates) * 0.65)], dates[int(len(dates) * 0.82)]
    train = joined[joined.session_date <= train_end]
    calibration = joined[
        (joined.session_date > train_end) & (joined.session_date <= calibration_end)
    ]
    test = joined[joined.session_date > calibration_end]
    pipeline = model_pipeline("logistic", columns, random_state=seed)
    model_start = time.perf_counter()
    pipeline.fit(train[columns], train[target])
    training_seconds = time.perf_counter() - model_start
    raw_cal = pipeline.predict_proba(calibration[columns])[:, 1]
    calibrator = ProbabilityCalibrator("sigmoid").fit(raw_cal, calibration[target])
    raw_test = pipeline.predict_proba(test[columns])[:, 1]
    probability = calibrator.predict(raw_test)
    baseline = UnconditionalClassifier().fit(train[columns], train[target])
    baseline_probability = baseline.predict_proba(test[columns])[:, 1]
    metrics = classification_metrics(test[target], probability)
    baseline_metrics = classification_metrics(test[target], baseline_probability)
    shuffled = train[target].sample(frac=1, random_state=seed).to_numpy()
    shuffled_model = model_pipeline("logistic", columns, random_state=seed).fit(
        train[columns], shuffled
    )
    shuffled_probability = shuffled_model.predict_proba(test[columns])[:, 1]
    shuffle_metrics = classification_metrics(test[target], shuffled_probability)
    output_root = Path(output_root)
    registry = ExperimentRegistry(output_root / "registry")
    experiment = PredictionExperiment(
        name="synthetic-edge" if planted_edge else "synthetic-null",
        hypothesis="Recover planted autoregressive relationship"
        if planted_edge
        else "No stable out-of-sample relationship",
        dataset_id=stable_hash(bars.to_dict("records")),
        feature_set_id=features.feature_set_hash,
        target_id=targets.target_set_hash,
        model_spec={"family": "logistic", "seed": seed},
        partition_spec={
            "train_end": str(train_end),
            "calibration_end": str(calibration_end),
            "test_end": str(dates[-1]),
            "chronological": True,
        },
        primary_metric="brier",
        secondary_metrics=("roc_auc", "pr_auc", "calibration_error"),
        baseline_models=("unconditional",),
        parameter_budget={"model_configurations": 1, "feature_sets": 1, "thresholds": 1},
        code_sha=code_sha,
    )
    if register:
        registry.register(experiment)
    artifact_dir = output_root / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{experiment.experiment_id}.joblib"
    joblib.dump({"pipeline": pipeline, "calibrator": calibrator}, artifact_path)
    result = {
        "label": "SYNTHETIC ENGINEERING EXPERIMENT — NOT MARKET EVIDENCE",
        "experiment": experiment.model_dump(mode="json"),
        "planted_edge": planted_edge,
        "sample_counts": {"train": len(train), "calibration": len(calibration), "test": len(test)},
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "shuffle_metrics": shuffle_metrics,
        "calibration_curve": calibration_curve_data(test[target], probability),
        "positive_rate_ci95": bootstrap_interval(test[target], samples=500, seed=seed),
        "explanation": linear_explanation(pipeline, columns),
        "artifact": {"uri": str(artifact_path), "sha256": file_hash(artifact_path)},
        "environment_hash": stable_hash({"python": sys.version, "platform": platform.platform()}),
        "timings_seconds": {
            "features": feature_seconds,
            "targets": target_seconds,
            "training": training_seconds,
            "total": time.perf_counter() - started,
        },
        "limitations": [
            "synthetic fixture",
            "not market evidence",
            "formal data gates remain blocked",
        ],
    }
    if register:
        result_path, result_hash = registry.write_result(experiment, result)
        result["result_artifact"] = {"uri": str(result_path), "sha256": result_hash}
    return result


def generate_report(result: dict, target: str | Path) -> Path:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    exp = result["experiment"]
    text = f"""# SYNTHETIC ENGINEERING EXPERIMENT — NOT MARKET EVIDENCE

## Hypothesis
{exp["hypothesis"]}

## Dataset and universe
Deterministic five-instrument fixture; dataset `{exp["dataset_id"]}`. No real-market universe.

## Target and features
Five-session direction target. Feature set `{exp["feature_set_id"]}`. Information boundary is after session close.

## Partitions / purge / embargo
Chronological training, calibration, and test partitions: `{json.dumps(exp["partition_spec"], sort_keys=True)}`. Formal target-overlap controls are provided by the partition engine.

## Model and baselines
Logistic regression with train-only imputation/scaling; unconditional base-rate baseline. Parameter budget: `{json.dumps(exp["parameter_budget"])}`.

## Results and calibration
Metrics: `{json.dumps(result["metrics"], sort_keys=True)}`. Baseline: `{json.dumps(result["baseline_metrics"], sort_keys=True)}`.

## Feature importance / stability
Standardized linear coefficients: `{json.dumps(result["explanation"], sort_keys=True)}`.

## Sanity and leakage checks
Shuffled-target metrics: `{json.dumps(result["shuffle_metrics"], sort_keys=True)}`. Future/target-derived feature names are rejected separately by the feature contract.

## Limitations and decision
This run validates machinery only. It is not evidence of market edge and cannot become customer-visible. Formal research remains blocked.

## Artifact hashes
Model: `{result["artifact"]["sha256"]}`.
"""
    target.write_text(text, encoding="utf-8")
    return target
