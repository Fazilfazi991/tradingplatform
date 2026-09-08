import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.create_deployment_evidence import main as create_evidence
from scripts.validate_deployment_evidence import DeploymentEvidence


def evidence(**updates):
    values = {
        "environment": "staging",
        "deployment_id": "deployment-new",
        "rollback_deployment_id": "deployment-previous",
        "commit_sha": "a" * 40,
        "url": "https://staging.verified-edge.example",
        "recorded_at": datetime(2026, 9, 8, tzinfo=UTC),
        "operator": "release-operator",
        "checks": {
            "environment_contract": "PASS",
            "public_routes": "PASS",
            "internal_auth_boundary": "PASS",
            "public_payload_boundary": "PASS",
            "security_headers": "PASS",
            "robots_sitemap_canonical": "PASS",
            "unknown_stock_404": "PASS",
            "console_network": "PASS",
            "rollback_rehearsal": "PASS",
        },
        "state_migration": "NOT_APPLICABLE",
    }
    values.update(updates)
    return DeploymentEvidence(**values)


def test_deployment_evidence_is_hash_sealed_and_https():
    item = evidence()
    assert len(item.artifact_hash) == 64
    assert DeploymentEvidence.model_validate_json(item.model_dump_json()) == item


@pytest.mark.parametrize(
    "url",
    ["http://verified-edge.example", "https://localhost", "https://127.0.0.1"],
)
def test_deployment_evidence_rejects_unsafe_origins(url):
    with pytest.raises(ValueError, match="deployment URL"):
        evidence(url=url)


def test_deployment_evidence_requires_distinct_rollback_and_all_checks():
    with pytest.raises(ValueError, match="rollback target"):
        evidence(rollback_deployment_id="deployment-new")
    checks = evidence().checks.model_dump()
    checks["public_payload_boundary"] = "FAIL"
    with pytest.raises(ValueError):
        evidence(checks=checks)


def test_deployment_evidence_detects_tampering():
    item = evidence()
    with pytest.raises(ValueError, match="hash mismatch"):
        DeploymentEvidence.model_validate(
            {**item.model_dump(), "deployment_id": "tampered"}
        )


def test_create_deployment_evidence_writes_valid_sealed_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "deployment-evidence.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "create_deployment_evidence.py",
            "--environment",
            "production",
            "--deployment-id",
            "deployment-new",
            "--rollback-deployment-id",
            "deployment-previous",
            "--commit-sha",
            "a" * 40,
            "--url",
            "https://verified-edge.example",
            "--operator",
            "release-operator",
            "--output",
            str(output),
        ],
    )

    assert create_evidence() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    validated = DeploymentEvidence.model_validate(payload)
    assert validated.environment == "production"
    assert validated.checks.rollback_rehearsal == "PASS"
    assert len(validated.artifact_hash) == 64
