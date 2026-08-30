from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def expected_calibration_error(y_true, probability, bins: int = 10) -> float:
    y = np.asarray(y_true)
    p = np.asarray(probability)
    indices = np.minimum((p * bins).astype(int), bins - 1)
    return float(
        sum(
            (indices == i).mean() * abs(y[indices == i].mean() - p[indices == i].mean())
            for i in range(bins)
            if (indices == i).any()
        )
    )


def classification_metrics(y_true, probability, threshold: float = 0.5) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probability, dtype=float)
    pred = (p >= threshold).astype(int)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-8, 1 - 1e-8))),
        "calibration_error": expected_calibration_error(y, p),
    }


def regression_metrics(y_true, prediction) -> dict[str, float]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(prediction, dtype=float)
    correlation = float(np.corrcoef(y, p)[0, 1]) if np.std(y) and np.std(p) else 0.0
    rank = float(spearmanr(y, p).statistic) if len(y) > 1 else 0.0
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(mean_squared_error(y, p) ** 0.5),
        "r2": float(r2_score(y, p)),
        "rank_correlation": rank,
        "directional_accuracy": float(np.mean(np.sign(y) == np.sign(p))),
        "prediction_actual_correlation": correlation,
    }


def prediction_deciles(y_true, prediction) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": y_true, "prediction": prediction}).dropna()
    frame["decile"] = pd.qcut(frame["prediction"], 10, labels=False, duplicates="drop") + 1
    return frame.groupby("decile", as_index=False).agg(
        mean_future_return=("actual", "mean"),
        median_future_return=("actual", "median"),
        sample_size=("actual", "size"),
    )


def bootstrap_interval(
    values, statistic=np.mean, *, samples: int = 1000, seed: int = 17, alpha: float = 0.05
) -> tuple[float, float]:
    value = np.asarray(values)
    rng = np.random.default_rng(seed)
    estimates = [
        statistic(rng.choice(value, size=len(value), replace=True)) for _ in range(samples)
    ]
    return float(np.quantile(estimates, alpha / 2)), float(np.quantile(estimates, 1 - alpha / 2))


def benjamini_hochberg(p_values) -> np.ndarray:
    p = np.asarray(p_values, float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    out = np.empty_like(adjusted)
    out[order] = np.clip(adjusted, 0, 1)
    return out


def holm(p_values) -> np.ndarray:
    p = np.asarray(p_values, float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.maximum.accumulate(ranked * (len(p) - np.arange(len(p))))
    out = np.empty_like(adjusted)
    out[order] = np.clip(adjusted, 0, 1)
    return out
