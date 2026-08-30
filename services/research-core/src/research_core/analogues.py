from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import t


@dataclass(frozen=True)
class AnalogueResult:
    matches: pd.DataFrame
    aggregate: dict[str, float]
    method: str


def find_analogues(
    states: pd.DataFrame,
    *,
    query_instrument: str,
    query_time: pd.Timestamp,
    feature_columns: list[str],
    target_column: str | None = None,
    method: str = "euclidean",
    k: int = 20,
    exclusion_sessions: int = 0,
) -> AnalogueResult:
    if method not in {"euclidean", "cosine"}:
        raise ValueError("method must be euclidean or cosine")
    frame = states.copy()
    frame["session_date"] = pd.to_datetime(frame["session_date"], utc=True)
    query_time = pd.Timestamp(query_time)
    query = frame.loc[
        (frame["instrument_id"] == query_instrument) & (frame["session_date"] == query_time)
    ]
    if len(query) != 1:
        raise ValueError("query state must resolve exactly once")
    cutoff = query_time - pd.offsets.BDay(exclusion_sessions)
    candidates = frame.loc[frame["session_date"] < cutoff].copy()
    candidates = candidates.dropna(subset=feature_columns)
    vector = query.iloc[0][feature_columns].astype(float).to_numpy()
    matrix = candidates[feature_columns].astype(float).to_numpy()
    if not len(matrix):
        return AnalogueResult(candidates, {"sample_size": 0.0}, method)
    mean = matrix.mean(axis=0)
    scale = matrix.std(axis=0, ddof=1)
    scale[scale == 0] = 1
    standardized = (matrix - mean) / scale
    q = (vector - mean) / scale
    if method == "euclidean":
        score = np.linalg.norm(standardized - q, axis=1)
        candidates["distance"] = score
        candidates["similarity"] = 1 / (1 + score)
        candidates = candidates.sort_values(["distance", "session_date", "instrument_id"])
    else:
        norms = np.linalg.norm(standardized, axis=1) * max(np.linalg.norm(q), 1e-12)
        score = np.divide(standardized @ q, norms, out=np.zeros(len(matrix)), where=norms != 0)
        candidates["similarity"] = score
        candidates["distance"] = 1 - score
        candidates = candidates.sort_values(
            ["similarity", "session_date", "instrument_id"], ascending=[False, True, True]
        )
    # Avoid clusters of overlapping windows for the same instrument.
    selected = []
    for _, row in candidates.iterrows():
        if any(
            old["instrument_id"] == row["instrument_id"]
            and abs((old["session_date"] - row["session_date"]).days) <= exclusion_sessions
            for old in selected
        ):
            continue
        selected.append(row)
        if len(selected) == k:
            break
    matches = pd.DataFrame(selected).reset_index(drop=True)
    aggregate = {"sample_size": float(len(matches))}
    if target_column and target_column in matches and len(matches):
        outcomes = matches[target_column].dropna().astype(float)
        aggregate.update(_aggregate(outcomes))
    return AnalogueResult(matches, aggregate, method)


def _aggregate(outcomes: pd.Series) -> dict[str, float]:
    if outcomes.empty:
        return {"sample_size": 0.0}
    n = len(outcomes)
    mean = float(outcomes.mean())
    sem = float(outcomes.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    margin = float(t.ppf(0.975, n - 1) * sem) if n > 1 else 0.0
    return {
        "sample_size": float(n),
        "positive_percentage": float((outcomes > 0).mean()),
        "negative_percentage": float((outcomes < 0).mean()),
        "mean_return": mean,
        "median_return": float(outcomes.median()),
        "q10": float(outcomes.quantile(0.1)),
        "q90": float(outcomes.quantile(0.9)),
        "ci95_low": mean - margin,
        "ci95_high": mean + margin,
    }
