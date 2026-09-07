from datetime import UTC, date, datetime
from itertools import pairwise
from uuid import uuid4

from verified_edge.domain import DailyBar, Instrument
from verified_edge.real_market import (
    CollectionMode,
    DatasetState,
    MappingStatus,
    daily_history_chunks,
    detect_revisions,
    map_current_universe,
    observed_exchange_sessions,
    real_market_manifest,
)


def test_mapping_uses_isin_then_exact_symbol_and_never_fuzzy():
    instruments = [Instrument(exchange="NSE", segment="NSE_EQ", symbol="NEW",
                              isin="INE1", provider_instrument_key="NSE_EQ|INE1")]
    result = map_current_universe({"OLD": {"isin": "INE1"}, "NE": {}}, instruments)
    by_symbol = {x.symbol: x for x in result}
    assert by_symbol["NE"].status == MappingStatus.UNMATCHED
    assert by_symbol["OLD"].status == MappingStatus.MATCHED and by_symbol["OLD"].anchor == "ISIN"


def test_ambiguous_mapping_is_explicit():
    instruments = [Instrument(exchange="NSE", segment="NSE_EQ", symbol="A",
                              provider_instrument_key=f"NSE_EQ|{x}") for x in ("1", "2")]
    result = map_current_universe({"A": {}}, instruments)[0]
    assert result.status == MappingStatus.AMBIGUOUS and len(result.candidates) == 2


def test_daily_chunks_are_contiguous_and_bounded():
    chunks = daily_history_chunks(date(2000, 1, 1), date(2026, 9, 6))
    assert chunks[0][0] == date(2000, 1, 1) and chunks[-1][1] == date(2026, 9, 6)
    assert all(right[0].toordinal() == left[1].toordinal() + 1 for left, right in pairwise(chunks))
    assert all((end - start).days <= 3660 for start, end in chunks)


def test_manifest_preserves_real_provenance_and_warnings():
    inst = uuid4()
    bar = DailyBar(instrument_id=inst, symbol="A", session_date=date(2026, 1, 2), open=1,
                   high=2, low=1, close=2, volume=1, provider="UPSTOX",
                   raw_observation_id=uuid4(), transformation_hash="x")
    kwargs = {"universe_manifest": {"source_sha256": "u"}, "bars": [bar],
              "payload_hashes": ["p"], "mapping_hash": "m",
              "created_at": datetime(2026, 1, 3, tzinfo=UTC),
              "state": DatasetState.RESEARCH_ELIGIBLE,
              "collection_mode": CollectionMode.BACKFILLED_MARKET_DATA,
              "quality_summary": {}, "corporate_action_coverage": {}}
    first, second = real_market_manifest(**kwargs), real_market_manifest(**kwargs)
    assert first["dataset_hash"] == second["dataset_hash"]
    assert "SURVIVORSHIP_BIASED_CURRENT_UNIVERSE" in first["warnings"]
    assert first["public_redistribution"] == "NOT_APPROVED"


def test_revision_ledger_never_silently_overwrites():
    stamp = datetime(2026, 1, 2, tzinfo=UTC)
    old = [{"timestamp": stamp, "provider_row": [stamp.isoformat(), 1]}]
    new = [{"timestamp": stamp, "provider_row": [stamp.isoformat(), 2]}]
    revision = detect_revisions(old, new)
    assert revision and revision[0]["old_hash"] != revision[0]["new_hash"]


def test_market_provider_interface_has_no_execution_methods():
    from verified_edge.providers.base import MarketDataProvider
    forbidden = {"place_order", "modify_order", "cancel_order", "create_gtt", "transfer_funds"}
    assert forbidden.isdisjoint(dir(MarketDataProvider))


def test_observed_calendar_includes_special_session_and_excludes_holiday():
    import pandas as pd

    frame = pd.DataFrame({
        "instrument_id": ["A", "B", "A", "B"],
        "session_date": ["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03"],
    })
    sessions = observed_exchange_sessions(frame)
    assert date(2026, 1, 3) in sessions  # observed Saturday special session
    assert date(2026, 1, 1) not in sessions  # no invented weekday session
