import json
from pathlib import Path

import pytest
from research_core.common import stable_hash
from research_core.forward_model import FrozenForwardModelArtifact
from research_core.forward_runtime import (
    ForwardPaperRuntime,
    ForwardRuntimeError,
    FrozenForwardPackage,
)
from research_core.forward_validation import ForwardValidationLedger
from research_core.prediction_v1 import FEATURES

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research" / "prediction-v1"


def test_committed_forward_artifact_is_sealed_portable_and_not_activated(tmp_path: Path) -> None:
    artifact = FrozenForwardModelArtifact.model_validate_json(
        (RESEARCH / "forward-model-v1.json").read_text(encoding="utf-8")
    )
    package = FrozenForwardPackage.model_validate_json(
        (RESEARCH / "forward-package-v1.json").read_text(encoding="utf-8")
    )
    config = json.loads((ROOT / "config" / "forward-paper.json").read_text(encoding="utf-8"))
    holdout = json.loads(
        (RESEARCH / "prediction-v1-holdout-report.json").read_text(encoding="utf-8")
    )

    assert artifact.dataset_hash == package.dataset_hash
    assert artifact.artifact_hash == package.model_hash
    assert artifact.feature_config_hash == package.feature_config_hash
    assert artifact.holdout_report_hash == stable_hash(holdout)
    assert artifact.feature_names == FEATURES
    assert package.approved is False
    assert artifact.forward_predictions_started is False
    assert config["enabled"] is False
    assert config["package_path"] is None

    for model in artifact.models:
        probability = model.probabilities({name: 0.0 for name in FEATURES})
        assert sum(probability) == pytest.approx(1.0)
        assert all(0.0 <= value <= 1.0 for value in probability)

    ledger = ForwardValidationLedger(tmp_path / "forward.sqlite3")
    try:
        with pytest.raises(ForwardRuntimeError, match="not approved"):
            ForwardPaperRuntime(ledger, package)
    finally:
        ledger.close()
    assert not (tmp_path / "forward.sqlite3-journal").exists()
