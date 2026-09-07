from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_core.prediction_v1 import atomic_json


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_decision(
    registration: dict[str, Any], walk: dict[str, Any], holdout: dict[str, Any]
) -> dict[str, Any]:
    criteria = registration["holdout_pass_criteria"]
    selected = {(row["horizon"], row["model"]): row for row in walk["aggregates"]}
    checks = []
    for row in holdout["results"]:
        validation = selected[(row["horizon"], row["model"])]
        log_improvement = row["baseline"]["log_loss"] - row["metrics"]["log_loss"]
        checks.append(
            {
                "horizon": row["horizon"],
                "brier_improvement": row["brier_improvement"],
                "log_loss_improvement": log_improvement,
                "ece": row["metrics"]["ece"],
                "positive_validation_folds_fraction": validation["positive_brier_folds"] / 3,
                "criteria_pass": (
                    row["brier_improvement"] >= criteria["brier_improvement_vs_unconditional"]
                    and log_improvement >= criteria["log_loss_improvement_vs_unconditional"]
                    and row["metrics"]["ece"] <= criteria["ece_max"]
                    and validation["positive_brier_folds"] / 3
                    >= criteria["positive_validation_folds_fraction_min"]
                ),
                "coverage": row["abstention"]["coverage"],
            }
        )
    return {
        "checks": checks,
        "all_preregistered_criteria_pass": all(row["criteria_pass"] for row in checks),
        "coverage_warning": "VERY_LOW_COVERAGE_1D_3D_5D",
        "interpretation": "Candidate evidence only; forward paper validation required.",
    }


def render_markdown(
    reg: dict[str, Any],
    walk: dict[str, Any],
    nulls: dict[str, Any],
    hold: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    selected = {(r["horizon"], r["model"]): r for r in walk["aggregates"]}
    rows = []
    for result in hold["results"]:
        validation = selected[(result["horizon"], result["model"])]
        rows.append(
            f"| {result['horizon']}D | {result['model']} | {validation['mean_metrics']['multiclass_brier']:.4f} | "
            f"{result['metrics']['multiclass_brier']:.4f} | {result['baseline']['multiclass_brier']:.4f} | "
            f"{result['metrics']['ece']:.4f} | {result['abstention']['coverage']:.2%} |"
        )
    return f"""# Prediction Engine V1 final research report

> INTERNAL EXPLORATORY RESEARCH — NOT FOR CUSTOMER USE OR TRADING

## Decision

`{hold["decision"]} / {hold["research_status"]}`. All preregistered holdout criteria passed: `{str(audit["all_preregistered_criteria_pass"]).lower()}`. This is not verified edge. Forward paper validation is mandatory and has not started.

## Dataset and registration

- Dataset: `{reg["dataset_hash"]}`; 442,837 rows, 200 current-universe symbols, 2016-09-07 through 2026-09-04.
- Registration: `{reg["registration_hash"]}`.
- Holdout: {hold["holdout"][0]} through {hold["holdout"][1]}; slice `{hold["holdout_slice_hash"]}`; access count `1`.
- Universe: `SURVIVORSHIP_BIASED_CURRENT_UNIVERSE`. Point-in-time membership is unavailable.
- Structural actions: {hold["corporate_action_policy"]["structural_actions"]} events and {hold["corporate_action_policy"]["excluded_rows"]} surrounding rows excluded. Adjustment semantics remain unverified.

## Walk-forward and sealed holdout

| Horizon | Candidate | Validation Brier | Holdout Brier | Baseline Brier | Holdout ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

Thirty-six preregistered model/fold evaluations were retained. The models were fitted on expanding history, calibrated on the preceding 126 sessions, and purged by the horizon. Rows are a temporally and cross-sectionally dependent panel, not IID observations.

## Calibration, abstention, and OOD

Sigmoid calibration was selected before holdout. Probability means estimated target-class probability—not confidence and not profit probability. The frozen abstention rule uses 0.45 maximum probability, 0.08 top-two separation, model-disagreement, data-quality, and train-relative OOD gates.

Coverage is extremely low for 1D, 3D, and 5D. That materially limits usefulness even though unconditional holdout metrics improved. Thresholds were not retuned after seeing this result.

## Null controls and multiplicity

Date-block circular label permutations were used instead of row shuffling. Four selected horizon hypotheses remained below 0.05 after BH and Holm adjustment. Experiment count: {nulls["multiple_testing"]["experiment_count"]}.

## Baselines and unsupported outputs

Unconditional class probability is the scored primary baseline. Market-direction, momentum, and mean-reversion rules are retained as research comparators in the architecture; sector-relative evaluation is unavailable because validated point-in-time sector membership is absent. Expected return, future range, and barrier probabilities remain nullable/disabled because no preregistered regression candidate was promoted in V1.

## Economic sanity

No execution or strategy backtest was built. Low/moderate/high friction assumptions of 10/25/50 bps are recorded only as sensitivity boundaries; the small discrimination improvements and low coverage do not support an economic edge claim.

## False-positive and stability warnings

- `SURVIVORSHIP_BIAS`
- `CORPORATE_ACTION_UNCERTAINTY`
- `MULTIPLE_TESTING_RISK`
- `VERY_LOW_COVERAGE_1D_3D_5D`
- `SINGLE_PROVIDER_INTERNAL_RESEARCH`
- `INTELLIGENCE_FEATURE_HISTORY_INSUFFICIENT`

No LLM generated a probability. Intelligence engines were excluded from training. No public output, BUY/SELL, target price, sizing, execution, or forward prediction was activated.
"""


def main() -> int:
    root = Path("research/prediction-v1")
    registration = read(root / "prediction-v1-registration.json")
    walk = read(root / "prediction-v1-walk-forward-report.json")
    nulls = read(root / "prediction-v1-null-controls.json")
    holdout = read(root / "prediction-v1-holdout-report.json")
    audit = audit_decision(registration, walk, holdout)
    if not audit["all_preregistered_criteria_pass"]:
        holdout["decision"] = "HOLDOUT_FAIL"
        holdout["research_status"] = "HOLDOUT_FAIL"
    holdout["criteria_audit"] = audit
    atomic_json(root / "prediction-v1-holdout-report.json", holdout)
    (root / "prediction-v1-final-research-report.md").write_text(
        render_markdown(registration, walk, nulls, holdout, audit), encoding="utf-8"
    )
    print(holdout["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
