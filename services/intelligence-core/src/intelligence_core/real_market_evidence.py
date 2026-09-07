from __future__ import annotations

from datetime import datetime
from typing import Any

from research_core.common import stable_hash

from intelligence_core.fusion import (
    EngineStatus,
    EvidenceOrientation,
    SpecialistEvidenceOutput,
)


def real_snapshot_evidence(snapshot: dict[str, Any], *, engine_id: str) -> SpecialistEvidenceOutput:
    available = snapshot.get("state") == "REAL_MARKET_DATA_INTERNAL"
    cutoff = snapshot["cutoff"]
    if not isinstance(cutoff, datetime) or cutoff.tzinfo is None:
        raise ValueError("real snapshot cutoff must be timezone-aware")
    return SpecialistEvidenceOutput(
        engine_id=engine_id, engine_family=f"{engine_id}_EVIDENCE", engine_version="real-market-v1",
        scope=f"ENTITY:{snapshot['entity']}", entity_id=snapshot["entity"], as_of=cutoff,
        horizon=str(snapshot.get("horizon", "1D")),
        status=EngineStatus.AVAILABLE if available else EngineStatus.INSUFFICIENT,
        evidence_orientation=EvidenceOrientation.NEUTRAL if available else EvidenceOrientation.INSUFFICIENT_EVIDENCE,
        certainty=0.5 if available else 0.0, data_quality="PASS" if available else "INSUFFICIENT",
        freshness=1.0 if available else 0.0, coverage=1.0 if available else 0.0,
        neutral_evidence=("REAL_MARKET_STATE_AVAILABLE",) if available else (),
        warnings=tuple(snapshot.get("warnings", ())),
        provenance={"dataset_id": snapshot.get("dataset_id"), "dataset_hash": snapshot.get("dataset_hash"),
                    "provider": "UPSTOX", "fixture_fallback": False},
        snapshot_hash=stable_hash(snapshot), source_quality=0.7, causal_integrity=1.0,
        sample_adequacy=min(1.0, float(snapshot.get("sample_adequacy", 1 if available else 0)) / 10),
        validation_status="NOT_PREDICTIVELY_VALIDATED",
        feature_families=("REAL_DAILY_OHLCV",), source_ids=("UPSTOX",),
    )
