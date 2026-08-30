from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


def synthetic_market_fixture(
    *, sessions: int = 320, instruments: int = 5, seed: int = 17, planted_edge: bool = True
) -> pd.DataFrame:
    """Deterministic fixture with controlled regimes/anomalies; never market evidence."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-02", periods=sessions, tz="UTC")
    records = []
    market_returns = rng.normal(0.0002, 0.008, sessions)
    market_close = 1000 * np.cumprod(1 + market_returns)
    for number in range(instruments):
        base_noise = 0.006 if planted_edge else 0.011
        noise = rng.normal(0, base_noise + number * 0.0005, sessions)
        returns = np.zeros(sessions)
        for index in range(1, sessions):
            autoregressive = 0.72 * returns[index - 1] if planted_edge else 0
            regime = (
                0.0012
                if planted_edge and 40 <= index < 110
                else -0.001
                if planted_edge and 110 <= index < 170
                else 0
            )
            market_component = 0.25 * market_returns[index] if planted_edge else 0
            returns[index] = autoregressive + regime + market_component + noise[index]
        returns[210:216] *= 3.5  # controlled volatility spike
        returns[250] += 0.075  # gap/breakout
        returns[251] -= 0.065  # sharp reversal / action-like discontinuity
        close = (90 + number * 18) * np.cumprod(1 + returns)
        open_ = np.r_[close[0], close[:-1] * (1 + rng.normal(0, 0.002, sessions - 1))]
        high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, sessions))
        low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, sessions))
        volume = rng.integers(700_000, 1_400_000, sessions).astype(float)
        volume[220] *= 8
        sector_close = market_close * np.cumprod(1 + rng.normal(0, 0.001, sessions))
        for index, day in enumerate(dates):
            if number == instruments - 1 and index == 180:  # deliberate missing session
                continue
            records.append(
                {
                    "instrument_id": f"SYNTH-{number + 1}",
                    "session_date": day,
                    "available_at": day + timedelta(hours=16),
                    "open": open_[index],
                    "high": high[index],
                    "low": low[index],
                    "close": close[index],
                    "volume": int(volume[index]),
                    "benchmark_close": market_close[index],
                    "sector_close": sector_close[index],
                    "corporate_action_like": index == 250,
                }
            )
    return pd.DataFrame(records)
