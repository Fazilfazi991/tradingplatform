"""Leakage-safe prediction research machinery for fixture engineering."""

from research_core.api import (
    build_feature_matrix,
    build_targets,
    calibrate_model,
    classify_regime,
    evaluate_predictions,
    find_analogues,
    generate_report,
    run_experiment,
)

__all__ = [
    "build_feature_matrix",
    "build_targets",
    "calibrate_model",
    "classify_regime",
    "evaluate_predictions",
    "find_analogues",
    "generate_report",
    "run_experiment",
]
