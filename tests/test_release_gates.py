from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.audit_release_gates import (
    GateManifestError,
    audit_manifest,
    release_authorization,
)

REPO = Path(__file__).resolve().parents[1]


def manifest() -> dict[str, object]:
    return json.loads((REPO / "config/release-gates.json").read_text(encoding="utf-8"))


def test_current_manifest_is_evidenced_and_fail_closed() -> None:
    report = audit_manifest(manifest(), repo=REPO)
    assert report["evidence_errors"] == []
    assert report["tracks"]["public_platform"]["decision"] == "PRODUCTION BLOCKED"
    assert report["tracks"]["promotion"]["decision"] == "PROMOTION BLOCKED"
    assert (
        report["tracks"]["prediction"]["decision"]
        == "HOLDOUT VALIDATED — FORWARD REQUIRED"
    )
    assert report["tracks"]["prediction"]["ready"] is False


def test_repository_security_is_partial_and_does_not_close_engineering() -> None:
    evidence = json.loads(
        (
            REPO
            / "research"
            / "release-readiness"
            / "repository-controls-2026-09-08.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["secret_protection_enabled"] is True
    assert evidence["push_protection_enabled"] is True
    assert evidence["rulesets_configured"] is False
    assert evidence["classic_branch_protection_configured"] is False

    current = manifest()
    engineering = next(gate for gate in current["gates"] if gate["id"] == "engineering")
    assert engineering["state"] == "EXTERNAL"
    assert "EXT-07" in engineering["blockers"]


def test_linked_hosting_root_is_reconciled_without_claiming_deployment() -> None:
    evidence = json.loads(
        (
            REPO
            / "research"
            / "release-readiness"
            / "hosting-project-2026-09-08.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["project_linked"] is True
    assert evidence["root_directory"] == "REPOSITORY_ROOT"
    assert evidence["deployment_triggered_by_reconciliation"] is False
    assert evidence["successful_staging_evidence"] is False
    assert evidence["successful_production_evidence"] is False
    assert evidence["canonical_domain_approved"] is False

    current = manifest()
    engineering = next(gate for gate in current["gates"] if gate["id"] == "engineering")
    assert engineering["state"] == "EXTERNAL"
    assert "EXT-06" in engineering["blockers"]


def test_codex_maintenance_contract_separates_review_from_runtime() -> None:
    text = (REPO / "CODEX_MAINTENANCE_AUTOMATIONS.md").read_text(encoding="utf-8")
    assert "verified-edge-daily-runtime-triage" in text
    assert "verified-edge-weekly-readiness-audit" in text
    assert "they do not collect market data" in text
    assert "cannot satisfy web uptime" in text
    assert "production worker supervision" in text


def test_open_branch_audit_does_not_hide_unmerged_functional_work() -> None:
    evidence = json.loads(
        (
            REPO
            / "research"
            / "release-readiness"
            / "git-branches-2026-09-08.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["canonical_branch"] == "main"
    assert evidence["unmerged_functional_work_detected"] is False
    assert evidence["destructive_cleanup_performed"] is False
    statuses = {branch["unique_patch_status"] for branch in evidence["branches"]}
    assert statuses == {"PATCH_EQUIVALENT_IN_MAIN", "NO_UNMERGED_PATCH"}


def test_release_environment_audit_is_names_only_and_fail_closed() -> None:
    evidence = json.loads(
        (
            REPO
            / "research"
            / "release-readiness"
            / "release-environments-2026-09-08.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["values_disclosed"] is False
    assert evidence["vercel"]["project_environment_variable_count"] == 0
    assert evidence["vercel"]["deployment_protection"]["enabled"] is True
    assert evidence["vercel"]["deployment_protection"]["generated_deployment_urls_protected"] is True
    assert evidence["vercel"]["deployment_protection"]["automation_bypass_secret_configured"] is False
    assert evidence["github"]["production_staging_exists"] is False
    assert evidence["github"]["production_exists"] is True
    assert evidence["github"]["production_required_reviewers"] is False
    assert evidence["github"]["production_secret_count"] == 0
    assert evidence["release_workflow_environment_contract_ready"] is False
    assert evidence["deployment_triggered"] is False


def test_unknown_state_is_rejected() -> None:
    changed = copy.deepcopy(manifest())
    changed["gates"][0]["state"] = "ALMOST_READY"
    with pytest.raises(GateManifestError, match="unsupported state"):
        audit_manifest(changed, repo=REPO)


def test_external_state_requires_registered_blocker() -> None:
    changed = copy.deepcopy(manifest())
    changed["gates"][0]["blockers"] = ["EXT-999"]
    with pytest.raises(GateManifestError, match="unknown blockers"):
        audit_manifest(changed, repo=REPO)


def test_pass_state_cannot_retain_external_blockers() -> None:
    changed = copy.deepcopy(manifest())
    changed["gates"][0]["state"] = "PASS"
    with pytest.raises(GateManifestError, match="PASS cannot retain blockers"):
        audit_manifest(changed, repo=REPO)


def test_current_public_track_is_not_authorized_for_release() -> None:
    report = audit_manifest(manifest(), repo=REPO)
    authorization = release_authorization(report, "public_platform")
    assert authorization == {
        "track": "public_platform",
        "authorized": False,
        "decision": "PRODUCTION BLOCKED",
        "nonpassing_gates": [
            "engineering",
            "public_safety",
            "product",
            "operations",
        ],
    }


def test_public_tracks_do_not_depend_on_predictive_data_qualification() -> None:
    current = manifest()
    public_required = current["tracks"]["public_platform"]["required_gates"]
    promotion_required = current["tracks"]["promotion"]["required_gates"]
    prediction_required = current["tracks"]["prediction"]["required_gates"]

    assert "predictive_data" not in public_required
    assert "predictive_data" not in promotion_required
    assert "intelligence" not in public_required
    assert "intelligence" not in promotion_required
    assert "predictive_data" in prediction_required

    predictive_data = next(
        gate for gate in current["gates"] if gate["id"] == "predictive_data"
    )
    assert {"EXT-02", "EXT-03", "EXT-04"}.issubset(predictive_data["blockers"])

    public_safety = next(
        gate for gate in current["gates"] if gate["id"] == "public_safety"
    )
    assert "EXT-01" not in public_safety["blockers"]
    assert "EXT-05" in public_safety["blockers"]


def test_unknown_release_track_is_rejected() -> None:
    report = audit_manifest(manifest(), repo=REPO)
    with pytest.raises(GateManifestError, match="unknown release track"):
        release_authorization(report, "not-a-track")


def test_missing_evidence_blocks_every_dependent_track() -> None:
    changed = copy.deepcopy(manifest())
    changed["gates"][0]["state"] = "PASS"
    changed["gates"][0]["blockers"] = []
    changed["gates"][0]["evidence"] = ["does-not-exist.txt"]
    changed["gates"][0]["assertions"] = []
    report = audit_manifest(changed, repo=REPO)
    assert report["evidence_errors"] == [
        "engineering:does-not-exist.txt:MISSING_OR_OUTSIDE_REPO"
    ]
    assert report["tracks"]["public_platform"]["ready"] is False
    assert report["tracks"]["promotion"]["ready"] is False


def test_decisive_json_assertion_failure_is_reported_and_blocks_track() -> None:
    changed = copy.deepcopy(manifest())
    prediction = next(gate for gate in changed["gates"] if gate["id"] == "prediction")
    assertion = next(
        item for item in prediction["assertions"] if item["json_path"] == "holdout_access_count"
    )
    assertion["equals"] = 2
    report = audit_manifest(changed, repo=REPO)
    assert report["evidence_errors"] == [
        (
            "prediction:research/prediction-v1/prediction-v1-holdout-report.json:"
            "holdout_access_count:ASSERTION_FAILED"
        )
    ]
    assert report["tracks"]["prediction"]["ready"] is False
