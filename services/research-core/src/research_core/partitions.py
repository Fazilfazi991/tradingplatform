from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from research_core.common import stable_hash
from research_core.objects import PartitionSpec


@dataclass(frozen=True)
class PartitionIndices:
    train: pd.Index
    calibration: pd.Index
    test: pd.Index


def partition_indices(
    index: pd.MultiIndex | pd.Index, spec: PartitionSpec, *, target_horizon: int
) -> PartitionIndices:
    dates = pd.DatetimeIndex(
        index.get_level_values("session_date") if isinstance(index, pd.MultiIndex) else index
    )
    train_mask = (dates >= spec.train_start) & (dates <= spec.train_end)
    test_mask = (dates >= spec.test_start) & (dates <= spec.test_end)
    purge = max(spec.purge_sessions, target_horizon)
    unique_dates = sorted(set(dates))
    test_position = unique_dates.index(
        min(date for date in unique_dates if date >= pd.Timestamp(spec.test_start))
    )
    purged_dates = set(unique_dates[max(0, test_position - purge) : test_position])
    train_mask &= ~dates.isin(purged_dates)
    embargo_dates = set(unique_dates[test_position : test_position + spec.embargo_sessions])
    test_mask &= ~dates.isin(embargo_dates)
    calibration_mask = pd.Series(False, index=range(len(dates))).to_numpy()
    if spec.calibration_start and spec.calibration_end:
        calibration_mask = (dates >= spec.calibration_start) & (dates <= spec.calibration_end)
        train_mask &= ~calibration_mask
        test_mask &= ~calibration_mask
    return PartitionIndices(index[train_mask], index[calibration_mask], index[test_mask])


def walk_forward_specs(
    dates: list[datetime],
    *,
    train_sessions: int,
    test_sessions: int,
    step_sessions: int,
    rolling: bool = False,
    purge_sessions: int = 0,
    embargo_sessions: int = 0,
) -> list[PartitionSpec]:
    ordered = sorted(set(dates))
    result: list[PartitionSpec] = []
    position = train_sessions
    while position + test_sessions <= len(ordered):
        train_start = ordered[max(0, position - train_sessions)] if rolling else ordered[0]
        result.append(
            PartitionSpec(
                name=f"walk-forward-{len(result) + 1}",
                train_start=train_start,
                train_end=ordered[position - 1],
                test_start=ordered[position],
                test_end=ordered[position + test_sessions - 1],
                purge_sessions=purge_sessions,
                embargo_sessions=embargo_sessions,
                expanding=not rolling,
            )
        )
        position += step_sessions
    return result


def partition_manifest(
    *,
    dataset_hash: str,
    universe_version: str,
    feature_set_hash: str,
    target_version: str,
    specs: list[PartitionSpec],
    code_sha: str,
) -> dict:
    manifest = {
        "dataset_hash": dataset_hash,
        "universe_version": universe_version,
        "feature_set_hash": feature_set_hash,
        "target_version": target_version,
        "partitions": [spec.model_dump(mode="json") for spec in specs],
        "code_sha": code_sha,
        "sealed": True,
    }
    manifest["sha256"] = stable_hash(manifest)
    return manifest
