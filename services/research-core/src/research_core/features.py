from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from research_core.common import stable_hash

FORBIDDEN_PATTERNS = (
    "future_",
    "target",
    "forward_",
    "post_event",
    "next_",
    "full_dataset",
    "revised_",
    "post_close",
    "global_rank",
)
REQUIRED = {
    "instrument_id",
    "session_date",
    "available_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


class LeakageError(ValueError):
    pass


@dataclass(frozen=True)
class FeatureMatrix:
    values: pd.DataFrame
    metadata: pd.DataFrame
    feature_set_hash: str
    version: str = "technical-v1"


def validate_feature_names(columns: Iterable[str]) -> None:
    offenders = sorted(
        column
        for column in columns
        if any(pattern in column.lower() for pattern in FORBIDDEN_PATTERNS)
    )
    if offenders:
        raise LeakageError(f"future/target-derived feature columns rejected: {offenders}")


def build_feature_matrix(
    bars: pd.DataFrame,
    *,
    information_cutoff: datetime | None = None,
    dataset_version: str = "fixture-v1",
) -> FeatureMatrix:
    missing = REQUIRED - set(bars.columns)
    if missing:
        raise ValueError(f"missing required bar columns: {sorted(missing)}")
    validate_feature_names(bars.columns)
    frame = bars.copy()
    frame["session_date"] = pd.to_datetime(frame["session_date"], utc=True)
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    if information_cutoff is not None:
        cutoff = pd.Timestamp(information_cutoff)
        if cutoff.tzinfo is None:
            raise ValueError("information_cutoff must be timezone-aware")
        frame = frame.loc[frame["available_at"] <= cutoff]
    if (frame["available_at"] < frame["session_date"]).any():
        raise LeakageError("bar cannot be available before its session timestamp")
    frame = frame.sort_values(["instrument_id", "session_date"]).drop_duplicates(
        ["instrument_id", "session_date"], keep=False
    )
    groups = []
    feature_columns: set[str] = set()
    for _, group in frame.groupby("instrument_id", sort=True):
        calculated = _technical_features(group.copy())
        groups.append(calculated)
        feature_columns.update(set(calculated.columns) - set(frame.columns))
    values = pd.concat(groups, ignore_index=True) if groups else frame
    validate_feature_names(feature_columns)
    feature_columns = set(feature_columns)
    metadata = values[["instrument_id", "session_date", "available_at"]].copy()
    metadata["feature_definition_version"] = "technical-v1"
    metadata["input_dataset_version"] = dataset_version
    metadata["input_start"] = values.groupby("instrument_id")["session_date"].transform("min")
    metadata["missing_data_state"] = values[list(feature_columns)].isna().sum(axis=1)
    metadata["quality_status"] = np.where(metadata["missing_data_state"] > 0, "INCOMPLETE", "PASS")
    metadata["implementation_version"] = "research-core/features.py:v1"
    selected = ["instrument_id", "session_date", *sorted(feature_columns)]
    result = values[selected].set_index(["instrument_id", "session_date"]).sort_index()
    identity = {
        "version": "technical-v1",
        "dataset": dataset_version,
        "columns": sorted(feature_columns),
    }
    return FeatureMatrix(result, metadata, stable_hash(identity))


def _technical_features(g: pd.DataFrame) -> pd.DataFrame:
    close = g["close"].astype(float)
    high = g["high"].astype(float)
    low = g["low"].astype(float)
    open_ = g["open"].astype(float)
    volume = g["volume"].astype(float)
    previous = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous).abs(), (low - previous).abs()], axis=1
    ).max(axis=1)
    atr14 = true_range.rolling(14, min_periods=14).mean()

    for horizon in (1, 2, 3, 5, 10, 20, 60):
        g[f"return_{horizon}"] = close.pct_change(horizon, fill_method=None)
    for window in (20, 50, 100, 200):
        average = close.rolling(window, min_periods=window).mean()
        g[f"sma_distance_pct_{window}"] = close / average - 1
    for window in (10, 20, 50):
        average = close.ewm(span=window, adjust=False, min_periods=window).mean()
        g[f"ema_distance_pct_{window}"] = close / average - 1
    g["roc_10"] = close.pct_change(10, fill_method=None)
    g["rsi_2"] = _rsi(close, 2)
    g["rsi_14"] = _rsi(close, 14)
    ema12 = close.ewm(span=12, adjust=False, min_periods=26).mean()
    ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    g["macd_atr"] = (ema12 - ema26) / atr14
    g["atr_14"] = atr14
    g["atr_price_14"] = atr14 / close
    for window in (10, 20, 60):
        g[f"realized_vol_{window}"] = g["return_1"].rolling(window, min_periods=window).std(
            ddof=1
        ) * np.sqrt(252)
    g["range_expansion"] = (high - low) / (high - low).rolling(20, min_periods=20).median()
    g["gap_atr"] = (open_ - previous) / atr14
    median_volume = volume.rolling(20, min_periods=20).median()
    mean_volume = volume.rolling(20, min_periods=20).mean()
    std_volume = volume.rolling(20, min_periods=20).std(ddof=1)
    g["volume_median_ratio_20"] = volume / median_volume
    g["volume_zscore_20"] = (volume - mean_volume) / std_volume
    g["traded_value_percentile_60"] = (close * volume).rolling(60, min_periods=20).rank(pct=True)
    g["volume_trend_20"] = (
        volume.rolling(10, min_periods=10).mean() / volume.rolling(20, min_periods=20).mean() - 1
    )
    for window in (20, 50, 100):
        rolling_high = high.rolling(window, min_periods=window).max()
        g[f"distance_high_{window}"] = close / rolling_high - 1
    for window in (20, 50):
        rolling_low = low.rolling(window, min_periods=window).min()
        g[f"distance_low_{window}"] = close / rolling_low - 1
    prior_high = high.shift(1).rolling(20, min_periods=20).max()
    g["breakout_20"] = (close > prior_high).astype(float).where(prior_high.notna())
    g["close_location"] = np.where(high > low, (close - low) / (high - low), np.nan)
    g["daily_range_atr"] = (high - low) / atr14
    for window in (20, 60, 252):
        rolling_peak = close.rolling(window, min_periods=window).max()
        g[f"drawdown_{window}"] = close / rolling_peak - 1
    if "benchmark_close" in g:
        benchmark = g["benchmark_close"].astype(float)
        for window in (20, 60):
            g[f"relative_strength_market_{window}"] = close.pct_change(
                window, fill_method=None
            ) - benchmark.pct_change(window, fill_method=None)
    if "sector_close" in g:
        sector = g["sector_close"].astype(float)
        for window in (20, 60):
            g[f"relative_strength_sector_{window}"] = close.pct_change(
                window, fill_method=None
            ) - sector.pct_change(window, fill_method=None)
            if "benchmark_close" in g:
                g[f"sector_strength_market_{window}"] = sector.pct_change(
                    window, fill_method=None
                ) - g["benchmark_close"].astype(float).pct_change(window, fill_method=None)
    return g


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = gain / loss
    result = 100 - 100 / (1 + rs)
    return result.mask((gain == 0) & (loss == 0), 50).mask((loss == 0) & (gain > 0), 100)
