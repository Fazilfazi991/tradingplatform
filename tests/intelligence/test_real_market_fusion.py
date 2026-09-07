from datetime import UTC, datetime

from intelligence_core.fusion import FusionState, fuse_specialist_outputs
from intelligence_core.real_market_evidence import real_snapshot_evidence

NOW = datetime(2026, 9, 7, tzinfo=UTC)


def snapshot(state="REAL_MARKET_DATA_INTERNAL"):
    return {"entity": "RELIANCE", "cutoff": NOW, "horizon": "5D", "state": state,
            "dataset_id": "real-1", "dataset_hash": "a" * 64, "warnings": []}


def test_real_technical_and_historical_can_enter_fusion_without_prediction_claim():
    technical = real_snapshot_evidence(snapshot(), engine_id="TECHNICAL")
    historical = real_snapshot_evidence(snapshot(), engine_id="HISTORICAL")
    fused = fuse_specialist_outputs((technical, historical), cutoff=NOW)
    assert fused.fusion_state in {FusionState.BALANCED, FusionState.ABSTAIN}
    assert all(x.validation_status == "NOT_PREDICTIVELY_VALIDATED" for x in fused.engine_snapshots)
    assert all(x.provenance["fixture_fallback"] is False for x in fused.engine_snapshots)


def test_missing_real_snapshot_never_falls_back_to_fixture():
    evidence = real_snapshot_evidence(snapshot("INSUFFICIENT"), engine_id="TECHNICAL")
    assert evidence.status == "INSUFFICIENT"
    assert evidence.evidence_orientation == "INSUFFICIENT_EVIDENCE"
