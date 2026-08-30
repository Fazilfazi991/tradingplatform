from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, LinearRegression, LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


class UnconditionalClassifier:
    def fit(self, x, y):
        self.rate_ = float(np.mean(y))
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x):
        return np.tile([1 - self.rate_, self.rate_], (len(x), 1))

    def predict(self, x):
        return np.full(len(x), int(self.rate_ >= 0.5))


class UnconditionalRegressor:
    def fit(self, x, y):
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, x):
        return np.full(len(x), self.mean_)


@dataclass(frozen=True)
class FrozenRuleModel:
    family: Literal["market_direction", "momentum", "mean_reversion"]

    def predict_score(self, frame):
        if self.family == "market_direction":
            return (frame["market_return_20"] > 0).astype(float).to_numpy()
        if self.family == "momentum":
            return (frame["return_20"] > 0).astype(float).to_numpy()
        return (frame["rsi_2"] < 10).astype(float).to_numpy()


def model_pipeline(family: str, feature_names: list[str], *, random_state: int = 17) -> Pipeline:
    preprocessing = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                feature_names,
            )
        ]
    )
    estimators = {
        "logistic": LogisticRegression(max_iter=1000, random_state=random_state),
        "linear": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "elastic_net": ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=random_state),
        "decision_tree": DecisionTreeClassifier(
            max_depth=4, min_samples_leaf=20, random_state=random_state
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=random_state, n_jobs=1
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=75, max_depth=2, random_state=random_state
        ),
    }
    if family not in estimators:
        raise ValueError(f"unsupported model family: {family}")
    return Pipeline([("preprocess", preprocessing), ("model", estimators[family])])


def linear_explanation(pipeline: Pipeline, feature_names: list[str], row=None) -> dict[str, float]:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "coef_"):
        raise ValueError("model has no linear coefficients")
    coefficients = np.ravel(model.coef_)
    if row is None:
        return dict(zip(feature_names, map(float, coefficients), strict=True))
    transformed = pipeline.named_steps["preprocess"].transform(row)
    contributions = np.ravel(transformed[0]) * coefficients
    return dict(zip(feature_names, map(float, contributions), strict=True))


def tree_explanation(pipeline: Pipeline, feature_names: list[str]) -> dict[str, float]:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        raise ValueError("model has no tree feature importance")
    return dict(zip(feature_names, map(float, model.feature_importances_), strict=True))
