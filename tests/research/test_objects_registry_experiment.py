from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from research_core.experiment import generate_report, run_synthetic_experiment
from research_core.objects import (
    FeatureDefinition,
    PartitionSpec,
    PredictionExperiment,
    PredictionRecord,
    TargetDefinition,
)
from research_core.registry import DuplicateExperimentError, ExperimentRegistry


def experiment():
    return PredictionExperiment(
        name="x",
        hypothesis="fixture",
        dataset_id="d",
        feature_set_id="f",
        target_id="t",
        model_spec={"family": "logistic"},
        partition_spec={"kind": "walk"},
        primary_metric="brier",
        code_sha="abc",
    )


def test_definition_and_experiment_hashes_are_stable():
    f = FeatureDefinition(
        feature_id="f",
        name="return",
        family="returns",
        description="one day",
        lookback=1,
        input_fields=("close",),
        minimum_history=2,
        implementation_path="features.py",
        code_sha="abc",
    )
    t = TargetDefinition(
        target_id="t",
        name="forward",
        description="future return",
        horizon=1,
        target_type="return",
        implementation_path="targets.py",
    )
    assert len(f.definition_hash) == len(t.definition_hash) == 64
    a = experiment()
    b = experiment()
    assert a.config_hash == b.config_hash


def test_prediction_record_cutoff_and_hash():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    from uuid import uuid4

    record = PredictionRecord(
        model_id=uuid4(),
        instrument_id="A",
        as_of=now,
        information_cutoff=now,
        target_definition="t",
        horizon=5,
        prediction_type="probability",
        raw_prediction=0.6,
        uncertainty={},
        evidence_snapshot={},
        feature_snapshot={},
        model_version="1",
        dataset_version="1",
    )
    assert len(record.payload_hash) == 64
    with pytest.raises(ValidationError, match="information_cutoff"):
        record.model_copy(update={"information_cutoff": now + timedelta(seconds=1)}).model_validate(
            record.model_dump() | {"information_cutoff": now + timedelta(seconds=1)}
        )


def test_partition_order_validation():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError, match="chronological"):
        PartitionSpec(
            name="bad",
            train_start=now,
            train_end=now + timedelta(days=2),
            test_start=now + timedelta(days=1),
            test_end=now + timedelta(days=3),
        )


def test_registry_is_immutable_and_duplicate_aware(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    exp = experiment()
    path = registry.register(exp)
    assert path.exists()
    with pytest.raises(DuplicateExperimentError):
        registry.register(exp)
    result_path, digest = registry.write_result(exp, {"ok": True})
    assert result_path.exists() and len(digest) == 64
    with pytest.raises(DuplicateExperimentError):
        registry.write_result(exp, {"ok": False})


@pytest.mark.slow
def test_synthetic_edge_null_and_shuffle_end_to_end(tmp_path):
    edge = run_synthetic_experiment(
        planted_edge=True, output_root=tmp_path / "edge", code_sha="fixture-sha"
    )
    null = run_synthetic_experiment(
        planted_edge=False, output_root=tmp_path / "null", code_sha="fixture-sha"
    )
    assert edge["label"].endswith("NOT MARKET EVIDENCE")
    assert edge["metrics"]["roc_auc"] > edge["baseline_metrics"]["roc_auc"]
    assert edge["metrics"]["roc_auc"] > edge["shuffle_metrics"]["roc_auc"]
    assert null["metrics"]["roc_auc"] < 0.7
    assert null["metrics"]["roc_auc"] - null["baseline_metrics"]["roc_auc"] < 0.2
    report = generate_report(edge, tmp_path / "report.md")
    text = report.read_text()
    assert "NOT MARKET EVIDENCE" in text and "Formal research remains blocked" in text
    assert Path(edge["artifact"]["uri"]).exists()
