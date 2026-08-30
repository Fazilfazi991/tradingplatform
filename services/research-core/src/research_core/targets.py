from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research_core.common import stable_hash


@dataclass(frozen=True)
class TargetMatrix:
    values: pd.DataFrame
    target_set_hash: str
    version: str = "targets-v1"


def build_targets(
    bars: pd.DataFrame,
    *,
    horizons: tuple[int, ...] = (1, 3, 5, 10),
    neutral_band: float = 0.0,
    upper_barrier: float = 0.04,
    lower_barrier: float = -0.02,
    barrier_horizon: int = 5,
) -> TargetMatrix:
    required = {"instrument_id", "session_date", "open", "high", "low", "close"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"missing required target columns: {sorted(missing)}")
    frame = bars.copy()
    frame["session_date"] = pd.to_datetime(frame["session_date"], utc=True)
    groups = []
    for _, group in frame.sort_values(["instrument_id", "session_date"]).groupby(
        "instrument_id", sort=True
    ):
        groups.append(
            _targets(
                group.copy(), horizons, neutral_band, upper_barrier, lower_barrier, barrier_horizon
            )
        )
    output = pd.concat(groups, ignore_index=True)
    columns = [c for c in output.columns if c.startswith("target_")]
    values = (
        output[["instrument_id", "session_date", *columns]]
        .set_index(["instrument_id", "session_date"])
        .sort_index()
    )
    return TargetMatrix(
        values,
        stable_hash(
            {
                "version": "targets-v1",
                "horizons": horizons,
                "neutral_band": neutral_band,
                "barriers": [upper_barrier, lower_barrier, barrier_horizon],
            }
        ),
    )


def _targets(
    g: pd.DataFrame,
    horizons: tuple[int, ...],
    neutral_band: float,
    upper: float,
    lower: float,
    barrier_horizon: int,
) -> pd.DataFrame:
    close = g["close"].astype(float)
    for horizon in horizons:
        future_return = close.shift(-horizon) / close - 1
        g[f"target_forward_return_{horizon}"] = future_return
        g[f"target_direction_{horizon}"] = np.select(
            [future_return > neutral_band, future_return < -neutral_band], [1, -1], default=0
        ).astype(float)
        g.loc[future_return.isna(), f"target_direction_{horizon}"] = np.nan
        future_highs = pd.concat([g["high"].shift(-step) for step in range(1, horizon + 1)], axis=1)
        future_lows = pd.concat([g["low"].shift(-step) for step in range(1, horizon + 1)], axis=1)
        g[f"target_mfe_{horizon}"] = future_highs.max(axis=1) / close - 1
        g[f"target_mae_{horizon}"] = future_lows.min(axis=1) / close - 1
        future_returns = pd.concat(
            [close.shift(-step) / close - 1 for step in range(1, horizon + 1)], axis=1
        )
        g[f"target_future_volatility_{horizon}"] = future_returns.std(axis=1, ddof=1)
    g[f"target_barrier_{barrier_horizon}"] = [
        _barrier(g, row, upper, lower, barrier_horizon) for row in range(len(g))
    ]
    return g


def _barrier(g: pd.DataFrame, row: int, upper: float, lower: float, horizon: int) -> float:
    if row + horizon >= len(g):
        return np.nan
    base = float(g.iloc[row]["close"])
    for offset in range(1, horizon + 1):
        bar = g.iloc[row + offset]
        # Conservative same-bar convention: adverse/lower barrier wins an ambiguous collision.
        if float(bar["low"]) / base - 1 <= lower:
            return -1.0
        if float(bar["high"]) / base - 1 >= upper:
            return 1.0
    return 0.0
