from __future__ import annotations

import json
import time
from pathlib import Path

from research_core.metrics import benjamini_hochberg, holm
from research_core.robustness import (
    NullKind,
    analogue_null_audit,
    distribution_summary,
    false_discovery_simulation,
    feature_mining_simulation,
    null_context,
    null_monte_carlo,
    selection_bias_simulation,
    signal_strength_curve,
    synthetic_panel,
    walk_forward_stability,
)


def main() -> None:
    started = time.perf_counter()
    output = Path("research/audits")
    output.mkdir(parents=True, exist_ok=True)
    seeds = range(1000)
    runs = null_monte_carlo(seeds, observations=1000, instruments=5)
    runs.to_csv(output / "null-monte-carlo-1000.csv", index=False)
    metrics = {
        name: distribution_summary(runs[name])
        for name in (
            "roc_auc",
            "pr_auc",
            "brier_improvement",
            "log_loss_improvement",
            "balanced_accuracy",
        )
    }
    tail = {
        f"p_auc_ge_{threshold}": float((runs.roc_auc >= threshold).mean())
        for threshold in (0.60, 0.64, 0.65, 0.70)
    }
    original_context = null_context(
        0.6405473587646204, runs.roc_auc, primary_improvement=-0.0009399611
    )
    print("completed primary 1,000-seed null Monte Carlo", flush=True)
    sample_sizes = {
        size: distribution_summary(null_monte_carlo(range(200), observations=size).roc_auc)
        for size in (500, 1000, 2500, 5000, 10000)
    }
    print("completed sample-size audit", flush=True)
    structured = {
        kind.value: distribution_summary(
            null_monte_carlo(range(200), observations=1000, instruments=20, kind=kind).roc_auc
        )
        for kind in NullKind
    }
    print("completed structured-null audit", flush=True)
    panel = {
        count: distribution_summary(
            null_monte_carlo(
                range(100), observations=5000, instruments=count, kind=NullKind.CROSS_SECTIONAL
            ).roc_auc
        )
        for count in (5, 20, 100, 200)
    }
    print("completed panel-dependence audit", flush=True)
    selection = selection_bias_simulation((1, 5, 10, 25, 50, 100))
    feature_mining = feature_mining_simulation((10, 50, 100, 500, 1000))
    print("completed selection and feature-mining audit", flush=True)
    strength = signal_strength_curve((0, 0.15, 0.3, 0.6, 1.0), range(250))
    print("completed signal-strength audit", flush=True)
    fdr = {
        "bh": false_discovery_simulation(adjuster=benjamini_hochberg),
        "holm": false_discovery_simulation(adjuster=holm),
    }
    analogue = analogue_null_audit(seeds=range(250))
    null_folds = walk_forward_stability(synthetic_panel(seed=17, observations=2500), folds=5)
    edge_folds = walk_forward_stability(
        synthetic_panel(seed=17, observations=2500, signal_strength=1.0), folds=5
    )
    result = {
        "label": "SYNTHETIC ROBUSTNESS AUDIT — NOT MARKET EVIDENCE",
        "runs": len(runs),
        "metrics": metrics,
        "tail_probabilities": tail,
        "original_null_context": original_context,
        "sample_sizes": sample_sizes,
        "structured_nulls": structured,
        "panel_structure": panel,
        "model_selection": selection,
        "feature_mining": feature_mining,
        "analogue_null": analogue,
        "walk_forward": {"null": null_folds, "planted": edge_folds},
        "signal_strength": strength,
        "multiple_testing": fdr,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output / "false-positive-summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
