from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pandas as pd
import pytest
from verified_edge.dataset import build_manifest, export_parquet, seal_manifest
from verified_edge.domain import DailyBar


def bar(symbol, day):
    return DailyBar(
        instrument_id=uuid4(),
        symbol=symbol,
        session_date=day,
        open=Decimal(100),
        high=Decimal(110),
        low=Decimal(90),
        close=Decimal(105),
        volume=1000,
        provider="FIXTURE",
        raw_observation_id=uuid4(),
        transformation_hash="a" * 64,
    )


def test_deterministic_parquet_export(tmp_path):
    bars = [bar("BETA", date(2026, 1, 5)), bar("ALPHA", date(2026, 1, 2))]
    _, hash1, count1 = export_parquet(bars, tmp_path / "one.parquet")
    _, hash2, count2 = export_parquet(list(reversed(bars)), tmp_path / "two.parquet")
    assert count1 == count2 == 2
    assert hash1 == hash2
    assert list(pd.read_parquet(tmp_path / "one.parquet")["symbol"]) == ["ALPHA", "BETA"]


def test_manifest_hash_deterministic_and_sealable():
    bars = [bar("ALPHA", date(2026, 1, 2))]
    args = {
        "purpose": "fixture",
        "universe": {"code": "TEST", "version": "1"},
        "bars": bars,
        "file_references": [{"path": "x.parquet", "sha256": "b" * 64}],
        "code_sha": "c" * 40,
        "trading_calendar_version": "1",
        "corporate_action_version": "NONE",
        "adjustment_version": "RAW",
        "quality_rules_version": "1",
        "created_at": datetime(2026, 1, 10, tzinfo=UTC),
    }
    first, second = build_manifest(**args), build_manifest(**args)
    assert first["dataset_id"] == second["dataset_id"]
    assert first["sha256"] == second["sha256"]
    sealed = seal_manifest(first, datetime(2026, 1, 11, tzinfo=UTC))
    assert sealed["sealed_at"] and sealed["sha256"] != first["sha256"]
    with pytest.raises(ValueError):
        seal_manifest(sealed)
