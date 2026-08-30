from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RegimeState:
    trend: str
    volatility: str
    breadth: str
    risk: str
    version: str = "deterministic-regime-v1"


def classify_regime(row: pd.Series | dict) -> RegimeState:
    value = dict(row)
    above_50 = value.get("index_vs_sma50", 0) > 0
    above_200 = value.get("index_vs_sma200", 0) > 0
    trend = (
        "BULL"
        if above_50 and above_200
        else "BEAR"
        if not above_50 and not above_200
        else "SIDEWAYS"
    )
    vol = (
        "HIGH"
        if value.get("volatility_percentile", 0.5) >= 0.8
        else "LOW"
        if value.get("volatility_percentile", 0.5) <= 0.2
        else "NORMAL"
    )
    breadth_value = value.get("breadth", 0.5)
    breadth = "STRONG" if breadth_value >= 0.6 else "WEAK" if breadth_value <= 0.4 else "MIXED"
    risk = (
        "RISK_OFF"
        if vol == "HIGH" and (trend == "BEAR" or breadth == "WEAK")
        else "RISK_ON"
        if trend == "BULL" and vol != "HIGH" and breadth != "WEAK"
        else "MIXED"
    )
    return RegimeState(trend, vol, breadth, risk)
