from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError
from research_core.metrics import benjamini_hochberg, holm
from research_core.objects import PredictionExperiment
from research_core.robustness import (
    ExperimentDecision,
    NullKind,
    analogue_null_audit,
    block_permutation_test,
    classify_experiment,
    distribution_summary,
    effective_sample_diagnostics,
    evaluate_panel,
    false_discovery_simulation,
    feature_mining_simulation,
    moving_block_auc_interval,
    null_context,
    null_monte_carlo,
    research_warnings,
    selection_bias_simulation,
    signal_strength_curve,
    synthetic_panel,
)


def test_null_generators_are_deterministic_and_structured():
    for kind in NullKind:
        first = synthetic_panel(seed=9, observations=500, instruments=5, kind=kind)
        second = synthetic_panel(seed=9, observations=500, instruments=5, kind=kind)
        assert first.equals(second)
        assert len(first) == 500 and first.instrument.nunique() == 5
        assert set(first.target.unique()) <= {0, 1}


def test_small_null_monte_carlo_centers_near_chance():
    runs = null_monte_carlo(range(30), observations=1000)
    assert len(runs) == 30
    assert 0.43 < runs.roc_auc.mean() < 0.57
    assert abs(runs.brier_improvement.mean()) < 0.02
    assert null_monte_carlo(range(3)).equals(null_monte_carlo(range(3)))


def test_distribution_summary_and_tail_shape():
    result = distribution_summary(range(100))
    assert result["median"] == pytest.approx(49.5)
    assert result["min"] == 0 and result["max"] == 99
    assert result["p5"] < result["p95"]
    context = null_context(0.64, np.linspace(0.4, 0.6, 100), primary_improvement=-0.01)
    assert context["conclusion"] == "NO EVIDENCE OF PREDICTIVE ADVANTAGE"
    assert context["null_percentile"] == 100


def test_block_permutation_is_deterministic_and_contextualizes_signal():
    rng = np.random.default_rng(5)
    y = rng.integers(0, 2, 400)
    score = y + rng.normal(0, 0.5, 400)
    first = block_permutation_test(y, score, permutations=100, seed=2)
    second = block_permutation_test(y, score, permutations=100, seed=2)
    assert first == second
    assert first["empirical_p"] < 0.05


def test_moving_block_auc_interval_contains_observed_signal():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 2, 300)
    score = y + rng.normal(0, 1, 300)
    low, high = moving_block_auc_interval(y, score, samples=100)
    observed = evaluate_panel(synthetic_panel(seed=2), seed=2).roc_auc
    assert 0 <= low < high <= 1
    assert 0 <= observed <= 1


def test_effective_sample_and_warning_policy():
    frame = synthetic_panel(seed=1, observations=500, instruments=20)
    diagnostics = effective_sample_diagnostics(frame, horizon=5)
    assert diagnostics["conservative_effective_n"] < diagnostics["rows"]
    assert "TARGET_OVERLAP" in diagnostics["warnings"]
    warnings = research_warnings(
        metrics={"brier": 0.26, "calibration_error": 0.12, "max_probability": 0.96},
        baseline={"brier": 0.25},
        fold_aucs=[0.3, 0.7],
        effective_n=30,
        attempts=5,
    )
    assert set(warnings) == {
        "NO_BASELINE_IMPROVEMENT",
        "POOR_CALIBRATION",
        "OVERCONFIDENT_MODEL",
        "INSUFFICIENT_SAMPLE",
        "UNSTABLE_ACROSS_FOLDS",
        "MULTIPLE_TESTING_RISK",
    }


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (
            {
                "engineering_ok": False,
                "synthetic_planted": False,
                "primary_improvement": 1,
                "empirical_p": 0.01,
                "stable": True,
            },
            ExperimentDecision.ENGINEERING_FAILURE,
        ),
        (
            {
                "engineering_ok": True,
                "synthetic_planted": False,
                "primary_improvement": -0.01,
                "empirical_p": 0.01,
                "stable": True,
            },
            ExperimentDecision.NO_EDGE,
        ),
        (
            {
                "engineering_ok": True,
                "synthetic_planted": False,
                "primary_improvement": 0.01,
                "empirical_p": 0.20,
                "stable": True,
            },
            ExperimentDecision.INCONCLUSIVE,
        ),
        (
            {
                "engineering_ok": True,
                "synthetic_planted": True,
                "primary_improvement": 0.01,
                "empirical_p": 0.01,
                "stable": True,
            },
            ExperimentDecision.SYNTHETIC_EXPECTED_EDGE,
        ),
    ],
)
def test_conservative_decision_policy(arguments, expected):
    assert classify_experiment(**arguments) == expected


def test_primary_metric_and_budget_are_preregistered():
    base = {
        "name": "x",
        "hypothesis": "h",
        "dataset_id": "d",
        "feature_set_id": "f",
        "target_id": "t",
        "model_spec": {},
        "partition_spec": {},
        "code_sha": "abc",
    }
    with pytest.raises(ValidationError, match="primary_metric"):
        PredictionExperiment(**base, primary_metric="whatever_looks_best")
    with pytest.raises(ValidationError, match="parameter_budget"):
        PredictionExperiment(
            **base, primary_metric="brier", parameter_budget={"model_configurations": 1}
        )
    first = PredictionExperiment(
        **base,
        primary_metric="brier",
        parameter_budget={"model_configurations": 1, "feature_sets": 1, "thresholds": 1},
    )
    second = PredictionExperiment(
        **base,
        primary_metric="brier",
        parameter_budget={"model_configurations": 2, "feature_sets": 1, "thresholds": 1},
    )
    assert first.config_hash != second.config_hash


def test_selection_bias_rises_with_attempts():
    result = selection_bias_simulation((1, 10, 100), repetitions=100, test_size=150)
    assert result[1]["median"] < result[10]["median"] < result[100]["median"]
    mined = feature_mining_simulation((10, 100), repetitions=50)
    assert mined[10]["median"] < mined[100]["median"]


def test_analogue_null_bias_centers_near_zero_and_low_k_is_noisier():
    result = analogue_null_audit(seeds=range(100))
    assert abs(result[100]["mean"]) < 0.03
    assert result[10]["std"] > result[200]["std"]


def test_signal_strength_curve_separates_null_from_strong():
    curve = signal_strength_curve((0, 0.5, 1.0), range(15), observations=800)
    assert curve[0]["mean"] < curve[0.5]["mean"] < curve[1.0]["mean"]


def test_multiple_testing_controls_known_vectors_and_all_null():
    values = [0.001, 0.01, 0.03, 0.5]
    assert np.allclose(benjamini_hochberg(values), [0.004, 0.02, 0.04, 0.5])
    assert np.allclose(holm(values), [0.004, 0.03, 0.06, 0.5])
    bh = false_discovery_simulation(repetitions=200, adjuster=benjamini_hochberg)
    family = false_discovery_simulation(repetitions=200, adjuster=holm)
    assert bh["runs_with_false_discovery"] < 0.10
    assert family["runs_with_false_discovery"] < 0.10


@pytest.mark.stress
def test_500_seed_null_stress_centers_on_chance():
    runs = null_monte_carlo(range(500), observations=1000)
    assert abs(runs.roc_auc.mean() - 0.5) < 0.02
    assert (runs.roc_auc >= 0.70).mean() < 0.01
