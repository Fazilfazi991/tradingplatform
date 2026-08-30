from datetime import UTC, datetime, timedelta
from itertools import pairwise

import pandas as pd
import pytest
from research_core.analogues import find_analogues
from research_core.objects import PartitionSpec
from research_core.partitions import partition_indices, partition_manifest, walk_forward_specs
from research_core.regimes import classify_regime


def states():
    dates = pd.bdate_range("2025-01-01", periods=20, tz="UTC")
    return pd.DataFrame(
        {
            "instrument_id": ["A"] * 20,
            "session_date": dates,
            "x": range(20),
            "y": [v % 4 for v in range(20)],
            "target": [(v - 10) / 100 for v in range(20)],
        }
    )


@pytest.mark.parametrize("method", ["euclidean", "cosine"])
def test_analogues_are_past_only_and_exclude_overlap(method):
    frame = states()
    query = frame.session_date.iloc[-1]
    result = find_analogues(
        frame,
        query_instrument="A",
        query_time=query,
        feature_columns=["x", "y"],
        target_column="target",
        method=method,
        k=4,
        exclusion_sessions=2,
    )
    assert len(result.matches) == 4
    assert (result.matches.session_date < query - pd.offsets.BDay(2)).all()
    assert result.aggregate["sample_size"] == 4
    assert "ci95_low" in result.aggregate
    dates = sorted(result.matches.session_date)
    assert all((b - a).days > 2 for a, b in pairwise(dates))


def test_analogue_input_validation_and_empty():
    frame = states()
    with pytest.raises(ValueError, match="method"):
        find_analogues(
            frame,
            query_instrument="A",
            query_time=frame.session_date.iloc[-1],
            feature_columns=["x"],
            method="bad",
        )
    early = find_analogues(
        frame,
        query_instrument="A",
        query_time=frame.session_date.iloc[0],
        feature_columns=["x"],
        k=2,
    )
    assert early.aggregate == {"sample_size": 0.0}


def test_partition_purge_embargo_and_manifest():
    dates = pd.bdate_range("2025-01-01", periods=30, tz="UTC")
    index = pd.MultiIndex.from_product([["A"], dates], names=["instrument_id", "session_date"])
    spec = PartitionSpec(
        name="one",
        train_start=dates[0].to_pydatetime(),
        train_end=dates[14].to_pydatetime(),
        test_start=dates[15].to_pydatetime(),
        test_end=dates[25].to_pydatetime(),
        purge_sessions=2,
        embargo_sessions=2,
    )
    result = partition_indices(index, spec, target_horizon=3)
    assert max(result.train.get_level_values("session_date")) == dates[11]
    assert min(result.test.get_level_values("session_date")) == dates[17]
    manifest = partition_manifest(
        dataset_hash="d",
        universe_version="fixture",
        feature_set_hash="f",
        target_version="t",
        specs=[spec],
        code_sha="abc",
    )
    assert manifest["sealed"] and len(manifest["sha256"]) == 64


def test_walk_forward_expanding_and_rolling():
    dates = [datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=i) for i in range(20)]
    expanding = walk_forward_specs(dates, train_sessions=10, test_sessions=3, step_sessions=3)
    rolling = walk_forward_specs(
        dates, train_sessions=10, test_sessions=3, step_sessions=3, rolling=True
    )
    assert len(expanding) == len(rolling) == 3
    assert expanding[1].train_start == dates[0]
    assert rolling[1].train_start == dates[3]


def test_regime_is_multi_axis():
    regime = classify_regime(
        {
            "index_vs_sma50": 0.1,
            "index_vs_sma200": 0.2,
            "volatility_percentile": 0.9,
            "breadth": 0.3,
        }
    )
    assert (regime.trend, regime.volatility, regime.breadth, regime.risk) == (
        "BULL",
        "HIGH",
        "WEAK",
        "RISK_OFF",
    )
