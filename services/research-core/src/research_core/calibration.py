from __future__ import annotations

from itertools import pairwise

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ProbabilityCalibrator:
    def __init__(self, method: str = "sigmoid") -> None:
        if method not in {"sigmoid", "isotonic"}:
            raise ValueError("method must be sigmoid or isotonic")
        self.method = method
        self.model = (
            LogisticRegression()
            if method == "sigmoid"
            else IsotonicRegression(out_of_bounds="clip")
        )

    def fit(self, raw_probability, target):
        probability = np.asarray(raw_probability, dtype=float)
        y = np.asarray(target, dtype=int)
        if self.method == "sigmoid":
            self.model.fit(probability.reshape(-1, 1), y)
        else:
            self.model.fit(probability, y)
        return self

    def predict(self, raw_probability):
        probability = np.asarray(raw_probability, dtype=float)
        if self.method == "sigmoid":
            return self.model.predict_proba(probability.reshape(-1, 1))[:, 1]
        return self.model.predict(probability)


def calibration_curve_data(y_true, probability, bins: int = 10) -> list[dict[str, float]]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(probability, dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    result = []
    for lower, upper in pairwise(edges):
        mask = (p >= lower) & (p < upper if upper < 1 else p <= upper)
        if mask.any():
            result.append(
                {
                    "predicted": float(p[mask].mean()),
                    "observed": float(y[mask].mean()),
                    "count": float(mask.sum()),
                }
            )
    return result
