from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from research_core.features import LeakageError, build_feature_matrix
from research_core.fixtures import synthetic_market_fixture
from research_core.targets import build_targets


@pytest.fixture(scope="module")
def fixture():
    return synthetic_market_fixture()


def test_fixture_has_controlled_shape_and_events(fixture):
    assert fixture.instrument_id.nunique() == 5
    assert len(fixture) == 1599
    assert fixture.corporate_action_like.sum() == 5
    assert fixture.groupby("instrument_id").size().min() == 319


def test_feature_catalog_and_metadata_are_deterministic(fixture):
    first = build_feature_matrix(fixture)
    second = build_feature_matrix(fixture)
    assert first.feature_set_hash == second.feature_set_hash
    required = {
        "return_1",
        "sma_distance_pct_20",
        "ema_distance_pct_10",
        "atr_14",
        "rsi_2",
        "realized_vol_20",
        "volume_zscore_20",
        "distance_high_50",
        "breakout_20",
        "relative_strength_market_20",
        "relative_strength_sector_60",
        "drawdown_252",
    }
    assert required <= set(first.values.columns)
    assert set(first.metadata.quality_status) <= {"PASS", "INCOMPLETE"}


def test_hand_checked_features_for_monotonic_series():
    dates = pd.bdate_range("2025-01-01", periods=30, tz="UTC")
    close = np.arange(100.0, 130.0)
    frame = pd.DataFrame(
        {
            "instrument_id": "A",
            "session_date": dates,
            "available_at": dates + pd.Timedelta(hours=16),
            "open": close - 0.5,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000,
        }
    )
    features = build_feature_matrix(frame).values.reset_index()
    row = features.iloc[-1]
    assert row.return_1 == pytest.approx(129 / 128 - 1)
    assert row.sma_distance_pct_20 == pytest.approx(129 / np.mean(np.arange(110, 130)) - 1)
    assert row.atr_14 == pytest.approx(2)
    assert row.rsi_14 == 100
    assert row.distance_high_20 == pytest.approx(129 / 130 - 1)


def test_information_cutoff_and_leakage_names(fixture):
    cutoff = fixture.session_date.sort_values().iloc[100] + timedelta(hours=16)
    result = build_feature_matrix(fixture, information_cutoff=cutoff)
    assert result.metadata.available_at.max() <= cutoff
    attacked = fixture.assign(future_close=fixture.close.shift(-1))
    with pytest.raises(LeakageError, match="future/target"):
        build_feature_matrix(attacked)
    with pytest.raises(ValueError, match="timezone"):
        build_feature_matrix(
            fixture,
            information_cutoff=datetime(2025, 1, 1),  # noqa: DTZ001 - verifies rejection
        )


def test_target_forward_return_direction_mfe_mae_and_barrier():
    dates = pd.bdate_range("2025-01-01", periods=6, tz="UTC")
    frame = pd.DataFrame(
        {
            "instrument_id": "A",
            "session_date": dates,
            "open": [100, 100, 103, 104, 102, 106],
            "high": [101, 105, 106, 105, 108, 107],
            "low": [99, 99, 102, 96, 101, 104],
            "close": [100, 104, 105, 100, 107, 106],
        }
    )
    targets = build_targets(
        frame,
        horizons=(1, 3, 5),
        neutral_band=0.02,
        upper_barrier=0.04,
        lower_barrier=-0.02,
        barrier_horizon=5,
    ).values.reset_index()
    first = targets.iloc[0]
    assert first.target_forward_return_1 == pytest.approx(0.04)
    assert first.target_direction_1 == 1
    assert first.target_forward_return_3 == pytest.approx(0)
    assert first.target_direction_3 == 0
    assert first.target_mfe_3 == pytest.approx(0.06)
    assert first.target_mae_3 == pytest.approx(-0.04)
    assert first.target_barrier_5 == 1  # upper is reached first on session 1
    assert np.isnan(targets.iloc[-1].target_forward_return_1)


def test_same_bar_barrier_collision_is_conservative():
    dates = pd.bdate_range("2025-01-01", periods=3, tz="UTC")
    frame = pd.DataFrame(
        {
            "instrument_id": "A",
            "session_date": dates,
            "open": [100] * 3,
            "high": [101, 106, 101],
            "low": [99, 97, 99],
            "close": [100] * 3,
        }
    )
    result = build_targets(
        frame, horizons=(1,), upper_barrier=0.04, lower_barrier=-0.02, barrier_horizon=1
    )
    assert result.values.iloc[0].target_barrier_1 == -1
