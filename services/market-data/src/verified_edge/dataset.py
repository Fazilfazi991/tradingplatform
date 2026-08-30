from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pandas as pd

from verified_edge.domain import DailyBar


def export_parquet(bars: Iterable[DailyBar], target: str | Path) -> tuple[Path, str, int]:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "instrument_id": str(b.instrument_id),
            "symbol": b.symbol,
            "session_date": b.session_date.isoformat(),
            "open": str(b.open),
            "high": str(b.high),
            "low": str(b.low),
            "close": str(b.close),
            "volume": b.volume,
            "provider": b.provider,
            "raw_observation_id": str(b.raw_observation_id),
            "canonical_version": b.canonical_version,
            "quality_status": b.quality_status.value,
            "transformation_hash": b.transformation_hash,
        }
        for b in sorted(bars, key=lambda x: (x.symbol, x.session_date))
    ]
    frame = pd.DataFrame.from_records(records)
    frame.to_parquet(target, engine="pyarrow", compression="zstd", index=False)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return target, digest, len(frame)


def build_manifest(
    *,
    purpose: str,
    universe: dict[str, Any],
    bars: Iterable[DailyBar],
    file_references: list[dict[str, Any]],
    code_sha: str,
    trading_calendar_version: str,
    corporate_action_version: str,
    adjustment_version: str,
    quality_rules_version: str,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    rows = list(bars)
    created_at = created_at or datetime.now(UTC)
    manifest = {
        "created_at": created_at.isoformat(),
        "purpose": purpose,
        "universe": universe,
        "date_range": {
            "start": min((b.session_date for b in rows), default=None),
            "end": max((b.session_date for b in rows), default=None),
        },
        "providers": sorted({b.provider for b in rows}),
        "instruments": sorted({str(b.instrument_id) for b in rows}),
        "canonical_versions": sorted({b.canonical_version for b in rows}),
        "trading_calendar_version": trading_calendar_version,
        "corporate_action_version": corporate_action_version,
        "adjustment_version": adjustment_version,
        "quality_rules_version": quality_rules_version,
        "code_sha": code_sha,
        "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "row_count": len(rows),
        "files": sorted(file_references, key=lambda x: x["path"]),
        "sealed_at": None,
    }
    identity_payload = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), default=_json_default
    )
    manifest["dataset_id"] = str(uuid5(NAMESPACE_URL, identity_payload))
    manifest["sha256"] = manifest_hash(manifest)
    return manifest


def manifest_hash(manifest: dict[str, Any]) -> str:
    value = {key: item for key, item in manifest.items() if key != "sha256"}
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=_json_default
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def seal_manifest(manifest: dict[str, Any], sealed_at: datetime | None = None) -> dict[str, Any]:
    if manifest.get("sealed_at"):
        raise ValueError("sealed dataset cannot mutate")
    sealed = dict(manifest)
    sealed["sealed_at"] = (sealed_at or datetime.now(UTC)).isoformat()
    sealed["sha256"] = manifest_hash(sealed)
    return sealed


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
