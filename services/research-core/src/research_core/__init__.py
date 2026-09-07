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
from research_core.prediction_v1 import public_prediction_guard, verify_frozen_dataset

__all__ = [
    "build_feature_matrix",
    "build_targets",
    "calibrate_model",
    "classify_regime",
    "evaluate_predictions",
    "find_analogues",
    "generate_report",
    "public_prediction_guard",
    "run_experiment",
    "verify_frozen_dataset",
]
