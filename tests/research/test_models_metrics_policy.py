from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from research_core.calibration import ProbabilityCalibrator, calibration_curve_data
from research_core.evidence import TechnicalEvidenceEngine
from research_core.future_sources import NewsFeatureExtractor
from research_core.metrics import (
    benjamini_hochberg,
    bootstrap_interval,
    classification_metrics,
    holm,
    prediction_deciles,
    regression_metrics,
)
from research_core.models import (
    FrozenRuleModel,
    UnconditionalClassifier,
    UnconditionalRegressor,
    linear_explanation,
    model_pipeline,
    tree_explanation,
)
from research_core.objects import ResearchMode
from research_core.policy import ResearchGateError, ResearchGatePolicy


def classification_data():
    rng = np.random.default_rng(4)
    x = pd.DataFrame({"a": rng.normal(size=160), "b": rng.normal(size=160)})
    y = (x.a + 0.2 * x.b > 0).astype(int)
    return x, y


@pytest.mark.parametrize(
    "family", ["logistic", "decision_tree", "random_forest", "gradient_boosting"]
)
def test_classification_model_families(family):
    x, y = classification_data()
    model = model_pipeline(family, ["a", "b"]).fit(x.iloc[:120], y.iloc[:120])
    probability = model.predict_proba(x.iloc[120:])[:, 1]
    assert classification_metrics(y.iloc[120:], probability)["roc_auc"] > 0.8
    if family == "logistic":
        assert set(linear_explanation(model, ["a", "b"])) == {"a", "b"}
    else:
        assert set(tree_explanation(model, ["a", "b"])) == {"a", "b"}


@pytest.mark.parametrize("family", ["linear", "ridge", "elastic_net"])
def test_regression_models_and_training_only_scaling(family):
    train = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0], "b": [1.0, 1.0, 2.0, 2.0]})
    test = pd.DataFrame({"a": [100.0], "b": [100.0]})
    y = np.array([0.0, 1.0, 2.0, 3.0])
    model = model_pipeline(family, ["a", "b"]).fit(train, y)
    scaler = model.named_steps["preprocess"].named_transformers_["numeric"].named_steps["scale"]
    assert scaler.mean_[0] == pytest.approx(1.5)
    assert np.isfinite(model.predict(test)).all()


def test_baselines_rules_calibration_and_curves():
    x, y = classification_data()
    base = UnconditionalClassifier().fit(x, y)
    assert np.allclose(base.predict_proba(x[:2])[:, 1], y.mean())
    assert UnconditionalRegressor().fit(x, [1, 2] * 80).predict(x[:1])[0] == 1.5
    rules = pd.DataFrame({"market_return_20": [1, -1], "return_20": [-1, 1], "rsi_2": [5, 50]})
    assert FrozenRuleModel("market_direction").predict_score(rules).tolist() == [1, 0]
    raw = np.linspace(0.05, 0.95, 100)
    target = (raw + np.random.default_rng(1).normal(0, 0.15, 100) > 0.5).astype(int)
    for method in ("sigmoid", "isotonic"):
        output = ProbabilityCalibrator(method).fit(raw[:70], target[:70]).predict(raw[70:])
        assert ((output >= 0) & (output <= 1)).all()
    assert sum(int(row["count"]) for row in calibration_curve_data(target, raw, 5)) == 100


def test_metrics_uncertainty_and_multiple_testing():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert classification_metrics(y, p)["brier"] < 0.1
    regression = regression_metrics([1, 2, 3], [1.1, 1.9, 3.1])
    assert regression["r2"] > 0.9
    assert len(prediction_deciles(np.arange(100), np.arange(100))) == 10
    low, high = bootstrap_interval([1, 2, 3, 4], samples=100)
    assert low < high
    assert (benjamini_hochberg([0.01, 0.04, 0.2]) <= 1).all()
    assert (holm([0.01, 0.04, 0.2]) <= 1).all()


def test_runtime_research_gate_and_future_source_cutoff():
    policy = ResearchGatePolicy.current()
    policy.authorize(ResearchMode.ENGINEERING_FIXTURE)
    with pytest.raises(ResearchGateError, match="point_in_time_universe"):
        policy.authorize(ResearchMode.FORMAL_DISCOVERY)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    observations = pd.DataFrame(
        {"available_at": [now - timedelta(seconds=1), now + timedelta(seconds=1)], "value": [1, 2]}
    )
    assert NewsFeatureExtractor().transform(observations, now).value.tolist() == [1]


def test_technical_evidence_is_research_only():
    features = pd.Series(
        {
            "sma_distance_pct_50": 0.1,
            "return_20": 0.05,
            "volume_median_ratio_20": 1.2,
            "atr_price_14": 0.05,
            "relative_strength_market_20": 0.02,
            "distance_high_20": -0.01,
        }
    )
    output = TechnicalEvidenceEngine().evaluate(
        features, as_of=datetime(2026, 1, 1, tzinfo=UTC), target="direction_5", horizon=5
    )
    assert output.status == "RESEARCH" and "volatility" in output.contradictions
