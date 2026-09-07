from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from research_core.common import stable_hash
from research_core.metrics import benjamini_hochberg, holm
from research_core.prediction_v1 import (
    FEATURES,
    HORIZONS,
    V1Paths,
    atomic_json,
    build_v1_frame,
    dataset_slice_hash,
    evaluate_candidate,
    load_bars,
    require_pre_holdout,
    serializable_result,
    structural_action_exclusions,
    verify_frozen_dataset,
)

MODELS = ("logistic", "regularized_logistic", "gradient_boosting")
FOLDS = (("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31"))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(paths: V1Paths) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    manifest = verify_frozen_dataset(paths)
    registration = read_json(paths.output / "prediction-v1-registration.json")
    cache = Path("data/local/prediction-v1/frame.parquet")
    policy_path = Path("data/local/prediction-v1/corporate-action-policy.json")
    if cache.exists() and policy_path.exists():
        import pandas as pd

        return pd.read_parquet(cache), manifest, read_json(policy_path)
    bars = load_bars(paths)
    excluded, policy = structural_action_exclusions(paths, bars)
    frame = build_v1_frame(bars, excluded)
    cache.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache, index=False)
    atomic_json(policy_path, policy)
    assert registration["dataset_hash"] == manifest["dataset_hash"]
    return frame, manifest, policy


def abstention_summary(result: dict[str, Any]) -> dict[str, Any]:
    p = result["probability"]
    sorted_p = np.sort(p, axis=1)
    low = p.max(axis=1) < 0.45
    narrow = (sorted_p[:, -1] - sorted_p[:, -2]) < 0.08
    strong_ood = result["ood_state"] == "STRONG_OOD"
    abstain = low | narrow | strong_ood
    covered = ~abstain
    metric = None
    if covered.any():
        from research_core.prediction_v1 import prediction_metrics

        metric = prediction_metrics(result["target"][covered], p[covered])
    return {
        "coverage": float(covered.mean()),
        "abstention_rate": float(abstain.mean()),
        "covered_metrics": metric,
        "reasons": {
            "low_probability": int(low.sum()),
            "low_separation": int(narrow.sum()),
            "strong_ood": int(strong_ood.sum()),
        },
    }


def null_control(result: dict[str, Any], seed: int = 17) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    y = result["target"]
    p = result["probability"]
    observed = result["baseline"]["multiclass_brier"] - result["metrics"]["multiclass_brier"]
    dates = np.asarray(result["dates"])
    unique_dates = np.unique(dates)
    scores = []
    for _ in range(100):
        shift = int(rng.integers(1, max(2, len(unique_dates))))
        mapping = dict(zip(unique_dates, np.roll(unique_dates, shift), strict=True))
        order = np.argsort(np.array([mapping[d] for d in dates]))
        permuted = y[order]
        one_hot = np.eye(3)[permuted]
        brier = float(np.mean(np.sum((p - one_hot) ** 2, axis=1)))
        scores.append(result["baseline"]["multiclass_brier"] - brier)
    p_value = float((1 + sum(score >= observed for score in scores)) / 101)
    return {
        "method": "date-block circular label permutation",
        "permutations": 100,
        "observed_brier_improvement": observed,
        "p_value": p_value,
        "random_feature_control": "EXCLUDED_BY_FROZEN_FEATURE_ALLOWLIST",
        "lagged_irrelevant_control": "covered by block-null test",
    }


def validation(paths: V1Paths) -> None:
    frame, manifest, corporate = prepare(paths)
    registration = read_json(paths.output / "prediction-v1-registration.json")
    results: list[dict[str, Any]] = []
    raw: dict[tuple[int, str, str], dict[str, Any]] = {}
    for horizon in HORIZONS:
        for model in MODELS:
            for start, end in FOLDS:
                print(f"validation {horizon}D {model} {start[:4]}", flush=True)
                result = evaluate_candidate(
                    frame, horizon=horizon, model_name=model, test_start=start, test_end=end
                )
                raw[(horizon, model, start)] = result
                item = serializable_result(result)
                item["fold"] = start[:4]
                results.append(item)
    aggregates = []
    for horizon in HORIZONS:
        for model in MODELS:
            rows = [row for row in results if row["horizon"] == horizon and row["model"] == model]
            aggregates.append(
                {
                    "horizon": horizon,
                    "model": model,
                    "mean_metrics": {
                        key: float(np.mean([row["metrics"][key] for row in rows]))
                        for key in rows[0]["metrics"]
                    },
                    "mean_baseline": {
                        key: float(np.mean([row["baseline"][key] for row in rows]))
                        for key in rows[0]["baseline"]
                    },
                    "positive_brier_folds": sum(
                        row["metrics"]["multiclass_brier"] < row["baseline"]["multiclass_brier"]
                        for row in rows
                    ),
                }
            )
    selected = []
    for horizon in HORIZONS:
        eligible = [row for row in aggregates if row["horizon"] == horizon]
        selected.append(min(eligible, key=lambda row: row["mean_metrics"]["multiclass_brier"]))
    nulls = []
    for candidate in selected:
        folds = [
            null_control(raw[(candidate["horizon"], candidate["model"], start)])
            for start, _ in FOLDS
        ]
        nulls.append(
            {
                "horizon": candidate["horizon"],
                "model": candidate["model"],
                "folds": folds,
                "mean_p_value": float(np.mean([f["p_value"] for f in folds])),
            }
        )
    p_values = [row["mean_p_value"] for row in nulls]
    adjusted_bh = benjamini_hochberg(p_values)
    adjusted_holm = holm(p_values)
    for row, bh, hm in zip(nulls, adjusted_bh, adjusted_holm, strict=True):
        row["bh_adjusted"] = float(bh)
        row["holm_adjusted"] = float(hm)
    holdout_hash = dataset_slice_hash(frame, "2025-01-01", "2026-09-04")
    report = {
        "label": "INTERNAL EXPLORATORY RESEARCH — NOT FOR TRADING",
        "registration_hash": registration["registration_hash"],
        "dataset_hash": manifest["dataset_hash"],
        "universe_state": "SURVIVORSHIP_BIASED_CURRENT_UNIVERSE",
        "features": list(FEATURES),
        "corporate_action_policy": corporate,
        "fold_results": results,
        "aggregates": aggregates,
        "sample_adequacy_warning": "PANEL_ROWS_ARE_CROSS_SECTIONALLY_AND_TEMPORALLY_DEPENDENT",
        "intelligence_features": "INTELLIGENCE_FEATURE_HISTORY_INSUFFICIENT",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "generated_at": datetime.now(UTC).isoformat(),
    }
    atomic_json(paths.output / "prediction-v1-walk-forward-report.json", report)
    atomic_json(
        paths.output / "prediction-v1-null-controls.json",
        {
            "controls": nulls,
            "multiple_testing": {"experiment_count": len(results), "methods": ["BH", "HOLM"]},
        },
    )
    decision = {
        "sealed": True,
        "registration_hash": registration["registration_hash"],
        "selected_candidates": [
            {
                "horizon": row["horizon"],
                "model": row["model"],
                "hyperparameters": registration["candidate_models"][row["model"]],
                "calibration": "sigmoid",
                "abstention": registration["abstention_policy"],
                "validation_metrics": row["mean_metrics"],
            }
            for row in selected
        ],
        "feature_version": registration["feature_version"],
        "target_version": registration["target_version"],
        "primary_metrics": registration["primary_metrics"],
        "expected_criteria": registration["holdout_pass_criteria"],
        "experiment_count": len(results),
        "holdout": registration["split_policy"]["sealed_holdout"],
        "holdout_slice_hash": holdout_hash,
        "created_at": datetime.now(UTC).isoformat(),
    }
    decision["decision_hash"] = stable_hash(decision)
    atomic_json(paths.output / "prediction-v1-pre-holdout-decision.json", decision)
    print("validation artifacts complete")


def holdout(paths: V1Paths) -> None:
    frame, _manifest, corporate = prepare(paths)
    registration = read_json(paths.output / "prediction-v1-registration.json")
    decision = require_pre_holdout(
        paths.output / "prediction-v1-pre-holdout-decision.json", registration["registration_hash"]
    )
    if dataset_slice_hash(frame, *decision["holdout"]) != decision["holdout_slice_hash"]:
        raise RuntimeError("sealed holdout slice hash mismatch")
    results = []
    for candidate in decision["selected_candidates"]:
        print(f"holdout {candidate['horizon']}D {candidate['model']}", flush=True)
        result = evaluate_candidate(
            frame,
            horizon=candidate["horizon"],
            model_name=candidate["model"],
            test_start=decision["holdout"][0],
            test_end=decision["holdout"][1],
        )
        item = serializable_result(result)
        item["abstention"] = abstention_summary(result)
        improvement = item["baseline"]["multiclass_brier"] - item["metrics"]["multiclass_brier"]
        item["brier_improvement"] = improvement
        item["friction_sensitivity"] = {
            "low_bps": 10,
            "moderate_bps": 25,
            "high_bps": 50,
            "research_note": "Forecast discrimination only; no strategy or execution backtest was constructed.",
        }
        results.append(item)
    criteria = registration["holdout_pass_criteria"]
    passing = [
        r
        for r in results
        if r["brier_improvement"] >= criteria["brier_improvement_vs_unconditional"]
        and r["metrics"]["ece"] <= criteria["ece_max"]
    ]
    state = (
        "HOLDOUT_PASS"
        if len(passing) == len(results)
        else ("HOLDOUT_FAIL" if not passing else "INCONCLUSIVE")
    )
    status = "FORWARD_VALIDATION_REQUIRED" if state == "HOLDOUT_PASS" else state
    report = {
        "label": "INTERNAL EXPLORATORY RESEARCH — NOT FOR TRADING",
        "holdout_access_count": 1,
        "holdout": decision["holdout"],
        "holdout_slice_hash": decision["holdout_slice_hash"],
        "registration_hash": registration["registration_hash"],
        "pre_holdout_decision_hash": decision["decision_hash"],
        "results": results,
        "decision": state,
        "research_status": status,
        "public_prediction": "BLOCKED",
        "forward_predictions_started": False,
        "survivorship_warning": "SURVIVORSHIP_BIASED_CURRENT_UNIVERSE",
        "corporate_action_policy": corporate,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "code_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    }
    atomic_json(paths.output / "prediction-v1-holdout-report.json", report)
    print(state)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("validation", "holdout"))
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("research/prediction-v1"))
    args = parser.parse_args()
    paths = V1Paths(args.dataset, args.output)
    validation(paths) if args.stage == "validation" else holdout(paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
