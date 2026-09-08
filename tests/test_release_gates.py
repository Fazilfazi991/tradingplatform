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
            "data",
            "intelligence",
            "public_safety",
            "product",
            "operations",
        ],
    }


def test_unknown_release_track_is_rejected() -> None:
    report = audit_manifest(manifest(), repo=REPO)
    with pytest.raises(GateManifestError, match="unknown release track"):
        release_authorization(report, "not-a-track")


def test_missing_evidence_blocks_every_dependent_track() -> None:
    changed = copy.deepcopy(manifest())
    changed["gates"][0]["state"] = "PASS"
    changed["gates"][0]["blockers"] = []
    changed["gates"][0]["evidence"] = ["does-not-exist.txt"]
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
