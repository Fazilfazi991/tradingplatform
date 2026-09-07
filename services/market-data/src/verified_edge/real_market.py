from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import Any

import numpy as np
import pandas as pd
from research_core.analogues import find_analogues
from research_core.features import build_feature_matrix

from verified_edge.domain import DailyBar, Instrument
from verified_edge.pipeline import canonicalize, make_raw_observations, stable_hash


class MappingStatus(StrEnum):
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"


class DatasetState(StrEnum):
    RAW = "RAW"
    QUALITY_CHECKED = "QUALITY_CHECKED"
    RESEARCH_ELIGIBLE = "RESEARCH_ELIGIBLE"
    QUARANTINED = "QUARANTINED"
    SUPERSEDED = "SUPERSEDED"


class CollectionMode(StrEnum):
    BACKFILLED_MARKET_DATA = "BACKFILLED_MARKET_DATA"
    FORWARD_COLLECTED_MARKET_DATA = "FORWARD_COLLECTED_MARKET_DATA"


@dataclass(frozen=True)
class MappingResult:
    symbol: str
    status: MappingStatus
    instrument: Instrument | None
    candidates: tuple[str, ...] = ()
    anchor: str | None = None


def map_current_universe(
    expected: dict[str, dict[str, Any]], instruments: list[Instrument]
) -> list[MappingResult]:
    """Resolve by ISIN first, exact NSE symbol second; never fuzzy match."""
    result = []
    for symbol, metadata in sorted(expected.items()):
        isin = metadata.get("isin")
        isin_matches = [
            item for item in instruments
            if isin and item.isin == isin and item.exchange == "NSE" and item.segment == "NSE_EQ"
        ]
        matches = isin_matches or [
            item for item in instruments
            if item.symbol == symbol and item.exchange == "NSE" and item.segment == "NSE_EQ"
        ]
        if len(matches) == 1:
            result.append(MappingResult(symbol, MappingStatus.MATCHED, matches[0],
                                        anchor="ISIN" if isin_matches else "EXACT_SYMBOL"))
        elif matches:
            result.append(MappingResult(symbol, MappingStatus.AMBIGUOUS, None,
                                        tuple(sorted(x.provider_instrument_key or "" for x in matches))))
        else:
            result.append(MappingResult(symbol, MappingStatus.UNMATCHED, None))
    return result


def daily_history_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Inclusive deterministic chunks no longer than one decade."""
    if start > end:
        raise ValueError("start must not follow end")
    chunks = []
    cursor = start
    while cursor <= end:
        try:
            boundary = cursor.replace(year=cursor.year + 10) - timedelta(days=1)
        except ValueError:
            boundary = cursor.replace(year=cursor.year + 10, day=28) - timedelta(days=1)
        chunk_end = min(end, boundary)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def canonicalize_provider_rows(
    instrument: Instrument, rows: list[dict[str, Any]], observed_at: datetime
) -> tuple[list[DailyBar], list[Any], list[Any]]:
    observations = make_raw_observations("UPSTOX", instrument, rows, observed_at=observed_at)
    return canonicalize(observations, {instrument.id: instrument})


def frame_for_research(bars: list[DailyBar], available_at: datetime) -> pd.DataFrame:
    if available_at.tzinfo is None:
        raise ValueError("available_at must be timezone-aware")
    return pd.DataFrame([
        {
            "instrument_id": str(bar.instrument_id),
            "session_date": datetime.combine(bar.session_date, datetime.min.time(), tzinfo=UTC),
            "available_at": available_at,
            "open": float(bar.open), "high": float(bar.high), "low": float(bar.low),
            "close": float(bar.close), "volume": bar.volume,
        }
        for bar in bars
    ])


def real_market_manifest(
    *, universe_manifest: dict[str, Any], bars: list[DailyBar], payload_hashes: list[str],
    mapping_hash: str, created_at: datetime, state: DatasetState,
    collection_mode: CollectionMode, quality_summary: dict[str, Any],
    corporate_action_coverage: dict[str, Any],
) -> dict[str, Any]:
    base = {
        "created_at": created_at.isoformat(), "provider": "UPSTOX",
        "provider_api": "Historical Candle V3 days/1",
        "universe_state": "CURRENT_UNIVERSE_SNAPSHOT",
        "universe_snapshot_hash": universe_manifest.get("source_sha256"),
        "instrument_mapping_hash": mapping_hash,
        "start_date": min((x.session_date for x in bars), default=None),
        "end_date": max((x.session_date for x in bars), default=None),
        "instrument_count": len({x.instrument_id for x in bars}), "bar_count": len(bars),
        "corporate_action_coverage": corporate_action_coverage,
        "quality_summary": quality_summary, "source_versions": ["UPSTOX_V3", "BOD_JSON"],
        "payload_hashes": sorted(payload_hashes), "state": state,
        "collection_mode": collection_mode, "research_mode": "EXPLORATORY_REAL_INTERNAL",
        "warnings": ["POINT_IN_TIME_UNIVERSE_UNAVAILABLE",
                     "SURVIVORSHIP_BIASED_CURRENT_UNIVERSE",
                     "PRICE_ADJUSTMENT_STATUS_UNVERIFIED",
                     "SINGLE_PROVIDER_INTERNAL_RESEARCH"],
        "public_redistribution": "NOT_APPROVED",
    }
    encoded = json.dumps(base, sort_keys=True, separators=(",", ":"), default=str).encode()
    base["dataset_hash"] = hashlib.sha256(encoded).hexdigest()
    base["dataset_id"] = base["dataset_hash"][:24]
    return base


def mapping_hash(results: list[MappingResult]) -> str:
    return stable_hash([
        {"symbol": x.symbol, "status": x.status, "key": x.instrument.provider_instrument_key
         if x.instrument else None, "anchor": x.anchor, "candidates": x.candidates}
        for x in results
    ])


def detect_revisions(old_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old = {str(x["timestamp"]): stable_hash(x.get("provider_row", x)) for x in old_rows}
    new = {str(x["timestamp"]): stable_hash(x.get("provider_row", x)) for x in new_rows}
    return [{"timestamp": key, "old_hash": old[key], "new_hash": new[key]}
            for key in sorted(old.keys() & new.keys()) if old[key] != new[key]]


def observed_exchange_sessions(
    bars: pd.DataFrame, *, minimum_instrument_fraction: float = 0.5
) -> set[date]:
    """Infer completed sessions from broad cross-sectional provider coverage.

    This includes special weekend sessions and excludes exchange holidays without
    pretending an ordinary weekday calendar is authoritative.
    """
    if not 0 < minimum_instrument_fraction <= 1:
        raise ValueError("minimum_instrument_fraction must be in (0, 1]")
    frame = bars.copy()
    frame["session_date"] = pd.to_datetime(frame["session_date"]).dt.date
    instrument_count = max(1, frame["instrument_id"].nunique())
    threshold = max(1, int(instrument_count * minimum_instrument_fraction))
    coverage = frame.groupby("session_date")["instrument_id"].nunique()
    return set(coverage[coverage >= threshold].index)


def build_technical_snapshot(
    entity: str, cutoff: datetime, bars: pd.DataFrame, *, dataset_id: str, dataset_hash: str
) -> dict[str, Any]:
    matrix = build_feature_matrix(bars, information_cutoff=cutoff, dataset_version=dataset_id)
    values = matrix.values.replace([np.inf, -np.inf], np.nan).dropna()
    selected = values.loc[values.index.get_level_values("instrument_id") == entity]
    selected = selected.loc[selected.index.get_level_values("session_date") <= cutoff]
    if selected.empty:
        return {"entity": entity, "cutoff": cutoff, "state": "INSUFFICIENT",
                "dataset_id": dataset_id, "dataset_hash": dataset_hash,
                "warnings": ["NO_COMPLETE_REAL_FEATURE_ROW"]}
    index = selected.index[-1]
    return {"entity": entity, "cutoff": cutoff, "feature_date": index[1],
            "state": "REAL_MARKET_DATA_INTERNAL", "validation": "NOT_PREDICTIVELY_VALIDATED",
            "features": selected.iloc[-1].to_dict(), "feature_set_hash": matrix.feature_set_hash,
            "dataset_id": dataset_id, "dataset_hash": dataset_hash,
            "warnings": ["SINGLE_PROVIDER_INTERNAL_RESEARCH"]}


def build_historical_analogue_snapshot(
    entity: str, cutoff: datetime, horizon: str, bars: pd.DataFrame, *, dataset_id: str,
    dataset_hash: str, k: int = 10,
) -> dict[str, Any]:
    technical = build_technical_snapshot(entity, cutoff, bars, dataset_id=dataset_id,
                                         dataset_hash=dataset_hash)
    if technical["state"] == "INSUFFICIENT":
        return {**technical, "horizon": horizon, "analogues": []}
    matrix = build_feature_matrix(bars, information_cutoff=cutoff, dataset_version=dataset_id)
    states = matrix.values.replace([np.inf, -np.inf], np.nan).dropna().reset_index()
    columns = [x for x in states.columns if x not in {"instrument_id", "session_date"}]
    query_time = pd.Timestamp(technical["feature_date"])
    result = find_analogues(states, query_instrument=entity, query_time=query_time,
                            feature_columns=columns, k=k, exclusion_sessions=10)
    if result.matches.empty:
        return {"entity": entity, "cutoff": cutoff, "horizon": horizon, "state": "INSUFFICIENT",
                "analogues": [], "dataset_id": dataset_id, "dataset_hash": dataset_hash,
                "warnings": ["INSUFFICIENT_PAST_ANALOGUES"]}
    if not (result.matches["session_date"] < query_time).all():
        raise ValueError("historical analogue must strictly precede cutoff")
    return {"entity": entity, "cutoff": cutoff, "horizon": horizon,
            "state": "REAL_MARKET_DATA_INTERNAL", "validation": "NOT_PREDICTIVELY_VALIDATED",
            "analogues": result.matches[["session_date", "distance", "similarity"]].to_dict("records"),
            "sample_adequacy": len(result.matches), "method": result.method,
            "dataset_id": dataset_id, "dataset_hash": dataset_hash,
            "warnings": ["SAME_SECURITY_HISTORY", "NO_PREDICTIVE_PROBABILITY"]}
