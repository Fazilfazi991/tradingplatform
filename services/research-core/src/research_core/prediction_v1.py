from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from research_core.common import stable_hash
from research_core.metrics import expected_calibration_error

EXPECTED_DATASET_HASH = "7ce7f964ca6aa8b551c68749e5f2d8a5a95e5e6c7b08005350807431fd866e6b"
HORIZONS = (1, 3, 5, 10)
FEATURE_VERSION = "prediction-v1-causal-technical-1"
TARGET_VERSION = "prediction-v1-volatility-neutral-1"
STRUCTURAL_ACTIONS = {"SPLIT", "BONUS", "RIGHTS", "DEMERGER", "MERGER", "FACE_VALUE_SPLIT"}
FEATURES = (
    "return_1",
    "return_3",
    "return_5",
    "return_10",
    "return_20",
    "sma_distance_20",
    "sma_distance_50",
    "ema_distance_20",
    "rsi_14",
    "atr_price_14",
    "realized_vol_20",
    "realized_vol_60",
    "volume_ratio_20",
    "volume_acceleration",
    "distance_high_60",
    "drawdown_60",
    "close_location",
    "market_return_20",
    "market_volatility_20",
    "relative_strength_market_20",
)


class DatasetFreezeError(RuntimeError):
    pass


class HoldoutAccessError(RuntimeError):
    pass


@dataclass(frozen=True)
class V1Paths:
    dataset: Path
    output: Path

    @property
    def bars(self) -> Path:
        return self.dataset / "canonical-daily-bars.parquet"

    @property
    def manifest(self) -> Path:
        return self.dataset / "dataset-manifest.json"

    @property
    def actions(self) -> Path:
        return self.dataset / "corporate-actions.json"


def verify_frozen_dataset(paths: V1Paths) -> dict[str, Any]:
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    if manifest.get("dataset_hash") != EXPECTED_DATASET_HASH:
        raise DatasetFreezeError("frozen dataset hash mismatch")
    if manifest.get("instrument_count") != 200 or manifest.get("bar_count") != 442_837:
        raise DatasetFreezeError("frozen dataset shape mismatch")
    return manifest


def build_registration(*, manifest: dict[str, Any], code_sha: str) -> dict[str, Any]:
    registration: dict[str, Any] = {
        "experiment_family_id": "PREDICTION_ENGINE_V1_REAL_MARKET",
        "dataset_hash": manifest["dataset_hash"],
        "universe_hash": manifest["universe_snapshot_hash"],
        "universe_state": "SURVIVORSHIP_BIASED_CURRENT_UNIVERSE",
        "feature_version": FEATURE_VERSION,
        "target_version": TARGET_VERSION,
        "split_policy": {
            "discovery": ["2016-09-07", "2021-12-31"],
            "walk_forward_validation": ["2022-01-01", "2024-12-31"],
            "sealed_holdout": ["2025-01-01", "2026-09-04"],
            "fold": "expanding annual validation blocks",
            "purge_sessions": 10,
            "embargo_sessions": 10,
            "shuffle": False,
        },
        "candidate_models": {
            "logistic": {"C": 1.0, "max_iter": 500},
            "regularized_logistic": {"C": 0.1, "max_iter": 500},
            "gradient_boosting": {"n_estimators": 75, "max_depth": 2},
        },
        "primary_metrics": ["multiclass_brier", "log_loss", "ece"],
        "secondary_metrics": ["balanced_accuracy", "cross_sectional_spearman_ic"],
        "calibration_method_candidates": ["sigmoid", "isotonic"],
        "selected_calibration_method": "sigmoid",
        "abstention_policy": {
            "minimum_top_probability": 0.45,
            "minimum_probability_separation": 0.08,
            "strong_ood": True,
            "maximum_model_disagreement": 0.18,
            "chosen_without_holdout": True,
        },
        "ood_policy": {
            "weak_extreme_features": 2,
            "strong_extreme_features": 4,
            "z_threshold": 4.0,
        },
        "multiple_testing_policy": ["BENJAMINI_HOCHBERG", "HOLM"],
        "holdout_pass_criteria": {
            "brier_improvement_vs_unconditional": 0.002,
            "log_loss_improvement_vs_unconditional": 0.002,
            "ece_max": 0.08,
            "positive_validation_folds_fraction_min": 0.60,
            "catastrophic_fold_brier_degradation_max": 0.02,
        },
        "corporate_action_policy": "EXCLUDE_STRUCTURAL_ACTION_WINDOWS_PLUS_MINUS_20_SESSIONS",
        "minimum_history_sessions": 252,
        "random_seeds": [17],
        "software_commit": code_sha,
        "prompt_or_llm_prediction": "PROHIBITED",
        "intelligence_feature_state": "INTELLIGENCE_FEATURE_HISTORY_INSUFFICIENT",
        "created_at": datetime.now(UTC).isoformat(),
        "sealed": True,
    }
    registration["registration_hash"] = stable_hash(registration)
    return registration


def write_registration(paths: V1Paths, registration: dict[str, Any]) -> Path:
    paths.output.mkdir(parents=True, exist_ok=True)
    target = paths.output / "prediction-v1-registration.json"
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing.get("registration_hash") != registration.get("registration_hash"):
            raise DatasetFreezeError("sealed registration cannot be replaced")
        return target
    target.write_text(json.dumps(registration, indent=2) + "\n", encoding="utf-8")
    return target


def load_bars(paths: V1Paths) -> pd.DataFrame:
    bars = pd.read_parquet(paths.bars)
    for column in ("open", "high", "low", "close", "volume"):
        bars[column] = pd.to_numeric(bars[column], errors="coerce")
    bars["session_date"] = pd.to_datetime(bars["session_date"], utc=True)
    return bars.sort_values(["instrument_id", "session_date"]).reset_index(drop=True)


def structural_action_exclusions(
    paths: V1Paths, bars: pd.DataFrame, radius: int = 20
) -> tuple[pd.Series, dict[str, Any]]:
    actions = json.loads(paths.actions.read_text(encoding="utf-8"))
    excluded = pd.Series(False, index=bars.index)
    count = 0
    for symbol, entries in actions.items():
        symbol_index = bars.index[bars["symbol"] == symbol]
        symbol_dates = bars.loc[symbol_index, "session_date"]
        for action in entries:
            if str(action.get("action_type", "")).upper() not in STRUCTURAL_ACTIONS or not len(
                symbol_index
            ):
                continue
            count += 1
            date = pd.Timestamp(action["effective_date"], tz="UTC")
            nearest = int(np.argmin(np.abs((symbol_dates - date).dt.days.to_numpy())))
            excluded.loc[symbol_index[max(0, nearest - radius) : nearest + radius + 1]] = True
    return excluded, {
        "policy": "EXCLUDE_STRUCTURAL_ACTION_WINDOWS_PLUS_MINUS_20_SESSIONS",
        "structural_actions": count,
        "excluded_rows": int(excluded.sum()),
        "remaining_uncertainty": "PRICE_ADJUSTMENT_STATUS_UNVERIFIED",
    }


def build_v1_frame(bars: pd.DataFrame, excluded: pd.Series) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for _, source in bars.groupby("instrument_id", sort=False):
        g = source.copy()
        close, high, low, volume = g.close, g.high, g.low, g.volume
        ret1 = close.pct_change(fill_method=None)
        for horizon in (1, 3, 5, 10, 20):
            g[f"return_{horizon}"] = close.pct_change(horizon, fill_method=None)
        g["sma_distance_20"] = close / close.rolling(20).mean() - 1
        g["sma_distance_50"] = close / close.rolling(50).mean() - 1
        g["ema_distance_20"] = close / close.ewm(span=20, adjust=False, min_periods=20).mean() - 1
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        g["rsi_14"] = 100 - 100 / (1 + gain / loss)
        prior = close.shift(1)
        tr = pd.concat([(high - low), (high - prior).abs(), (low - prior).abs()], axis=1).max(
            axis=1
        )
        g["atr_price_14"] = tr.rolling(14).mean() / close
        g["realized_vol_20"] = ret1.rolling(20).std() * np.sqrt(252)
        g["realized_vol_60"] = ret1.rolling(60).std() * np.sqrt(252)
        g["volume_ratio_20"] = volume / volume.rolling(20).median()
        g["volume_acceleration"] = volume.rolling(5).mean() / volume.rolling(20).mean() - 1
        g["distance_high_60"] = close / high.rolling(60).max() - 1
        g["drawdown_60"] = close / close.rolling(60).max() - 1
        g["close_location"] = np.where(high > low, (close - low) / (high - low), np.nan)
        g["history_count"] = np.arange(1, len(g) + 1)
        daily_vol = ret1.rolling(20).std().shift(1)
        for horizon in HORIZONS:
            forward = close.shift(-horizon) / close - 1
            neutral = daily_vol * np.sqrt(horizon) * 0.25
            g[f"target_return_{horizon}"] = forward
            g[f"target_direction_{horizon}"] = np.select(
                [forward < -neutral, forward > neutral], [0, 2], default=1
            )
            g.loc[forward.isna() | neutral.isna(), f"target_direction_{horizon}"] = np.nan
            future_high = pd.concat([high.shift(-i) for i in range(1, horizon + 1)], axis=1)
            future_low = pd.concat([low.shift(-i) for i in range(1, horizon + 1)], axis=1)
            paths = pd.concat([close.shift(-i) / close - 1 for i in range(1, horizon + 1)], axis=1)
            g[f"target_mfe_{horizon}"] = future_high.max(axis=1) / close - 1
            g[f"target_mae_{horizon}"] = future_low.min(axis=1) / close - 1
            g[f"target_volatility_{horizon}"] = paths.std(axis=1)
        parts.append(g)
    frame = pd.concat(parts, ignore_index=True)
    market = frame.groupby("session_date")["return_1"].median().sort_index()
    market20 = (1 + market).rolling(20).apply(np.prod, raw=True) - 1
    frame["market_return_20"] = frame.session_date.map(market20)
    frame["market_volatility_20"] = frame.session_date.map(market.rolling(20).std() * np.sqrt(252))
    frame["relative_strength_market_20"] = frame.return_20 - frame.market_return_20
    frame["corporate_action_excluded"] = excluded.to_numpy()
    return frame


def model_pipeline(name: str) -> Pipeline:
    if name == "logistic":
        estimator = LogisticRegression(C=1.0, max_iter=500, random_state=17)
    elif name == "regularized_logistic":
        estimator = LogisticRegression(C=0.1, max_iter=500, random_state=17)
    elif name == "gradient_boosting":
        estimator = GradientBoostingClassifier(n_estimators=75, max_depth=2, random_state=17)
    else:
        raise ValueError(f"unknown model: {name}")
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", estimator),
        ]
    )


def prediction_metrics(
    y: np.ndarray,
    probability: np.ndarray,
    returns: np.ndarray | None = None,
    dates: pd.Series | None = None,
) -> dict[str, float]:
    one_hot = np.eye(3)[y]
    result = {
        "multiclass_brier": float(np.mean(np.sum((probability - one_hot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, probability, labels=[0, 1, 2])),
        "balanced_accuracy": float(balanced_accuracy_score(y, probability.argmax(axis=1))),
        "ece": float(
            np.mean(
                [
                    expected_calibration_error((y == i).astype(int), probability[:, i])
                    for i in range(3)
                ]
            )
        ),
    }
    if returns is not None and dates is not None:
        temp = pd.DataFrame(
            {
                "date": dates.to_numpy(),
                "score": probability[:, 2] - probability[:, 0],
                "return": returns,
            }
        )
        values = [
            spearmanr(g.score, g["return"]).statistic
            for _, g in temp.groupby("date")
            if len(g) >= 10 and g.score.nunique() > 1
        ]
        result["cross_sectional_spearman_ic"] = float(np.nanmean(values)) if values else 0.0
    return result


def fit_calibrators(raw: np.ndarray, y: np.ndarray) -> list[LogisticRegression]:
    return [
        LogisticRegression(max_iter=300).fit(raw[:, [i]], (y == i).astype(int)) for i in range(3)
    ]


def apply_calibrators(models: list[LogisticRegression], raw: np.ndarray) -> np.ndarray:
    values = np.column_stack(
        [model.predict_proba(raw[:, [i]])[:, 1] for i, model in enumerate(models)]
    )
    return values / values.sum(axis=1, keepdims=True)


def evaluate_candidate(
    frame: pd.DataFrame, *, horizon: int, model_name: str, test_start: str, test_end: str
) -> dict[str, Any]:
    target, outcome = f"target_direction_{horizon}", f"target_return_{horizon}"
    eligible = (
        frame[(frame.history_count >= 252) & ~frame.corporate_action_excluded]
        .dropna(subset=[*FEATURES, target, outcome])
        .copy()
    )
    start, end = pd.Timestamp(test_start, tz="UTC"), pd.Timestamp(test_end, tz="UTC")
    test = eligible[(eligible.session_date >= start) & (eligible.session_date <= end)]
    past_dates = sorted(eligible.loc[eligible.session_date < start, "session_date"].unique())
    if len(past_dates) < 300 or test.empty:
        raise ValueError("insufficient chronological sample")
    calibration_dates = set(past_dates[-126:])
    purge_dates = set(past_dates[-(126 + horizon) : -126])
    calibration = eligible[eligible.session_date.isin(calibration_dates)]
    train = eligible[
        (eligible.session_date < min(calibration_dates)) & ~eligible.session_date.isin(purge_dates)
    ]
    model = model_pipeline(model_name).fit(train[list(FEATURES)], train[target].astype(int))
    raw_cal = model.predict_proba(calibration[list(FEATURES)])
    calibrators = fit_calibrators(raw_cal, calibration[target].astype(int).to_numpy())
    raw = model.predict_proba(test[list(FEATURES)])
    probability = apply_calibrators(calibrators, raw)
    base_rates = (
        train[target].value_counts(normalize=True).reindex([0, 1, 2], fill_value=0).to_numpy()
    )
    baseline = np.tile(base_rates, (len(test), 1))
    return {
        "horizon": horizon,
        "model": model_name,
        "sample": {
            "train": len(train),
            "calibration": len(calibration),
            "test": len(test),
            "symbols": int(test.instrument_id.nunique()),
            "dates": int(test.session_date.nunique()),
        },
        "metrics": prediction_metrics(
            test[target].astype(int).to_numpy(),
            probability,
            test[outcome].to_numpy(),
            test.session_date,
        ),
        "uncalibrated_metrics": prediction_metrics(test[target].astype(int).to_numpy(), raw),
        "baseline": prediction_metrics(test[target].astype(int).to_numpy(), baseline),
        "class_balance": {
            str(int(k)): float(v)
            for k, v in test[target].value_counts(normalize=True).sort_index().items()
        },
        "probability": probability,
        "target": test[target].astype(int).to_numpy(),
        "returns": test[outcome].to_numpy(),
        "dates": test.session_date,
    }


def serializable_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key not in {"probability", "target", "returns", "dates"}
    }


def require_pre_holdout(path: Path, registration_hash: str) -> dict[str, Any]:
    if not path.exists():
        raise HoldoutAccessError("pre-holdout decision required")
    decision = json.loads(path.read_text(encoding="utf-8"))
    if decision.get("registration_hash") != registration_hash or not decision.get("sealed"):
        raise HoldoutAccessError("invalid pre-holdout decision")
    return decision


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    temporary.replace(path)


def dataset_slice_hash(frame: pd.DataFrame, start: str, end: str) -> str:
    selected = frame[
        (frame.session_date >= pd.Timestamp(start, tz="UTC"))
        & (frame.session_date <= pd.Timestamp(end, tz="UTC"))
    ][["instrument_id", "session_date", "close"]]
    return stable_hash(selected.astype(str).to_dict("records"))


def public_prediction_guard(*, destination: str) -> None:
    if destination.upper() not in {"INTERNAL_RESEARCH", "RESEARCH_REGISTRY"}:
        raise PermissionError("PredictionResearchOutput is internal research only")
