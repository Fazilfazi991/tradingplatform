from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ALLOWED_STATES = {"PASS", "FAIL", "EXTERNAL"}


class GateManifestError(ValueError):
    """The release manifest is internally inconsistent or unsupported."""


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _external_blocker_ids(repo: Path) -> set[str]:
    text = (repo / "EXTERNAL_BLOCKERS.md").read_text(encoding="utf-8")
    return {
        field.strip()
        for line in text.splitlines()
        if line.startswith("|")
        for field in line.split("|")[1:2]
        if field.strip().startswith("EXT-")
    }


def audit_manifest(manifest: dict[str, Any], *, repo: Path) -> dict[str, Any]:
    if manifest.get("schema_version") != "release-gates-v1":
        raise GateManifestError("unsupported schema_version")
    declared_states = set(manifest.get("allowed_gate_states", []))
    if declared_states != ALLOWED_STATES:
        raise GateManifestError("allowed_gate_states must exactly match the policy")

    gates = manifest.get("gates")
    tracks = manifest.get("tracks")
    if not isinstance(gates, list) or not gates or not isinstance(tracks, dict):
        raise GateManifestError("gates and tracks are required")

    blocker_ids = _external_blocker_ids(repo)
    gate_map: dict[str, dict[str, Any]] = {}
    evidence_errors: list[str] = []
    for gate in gates:
        gate_id = gate.get("id")
        state = gate.get("state")
        if not isinstance(gate_id, str) or not gate_id or gate_id in gate_map:
            raise GateManifestError("gate ids must be unique non-empty strings")
        if state not in ALLOWED_STATES:
            raise GateManifestError(f"{gate_id}: unsupported state")
        if not isinstance(gate.get("reason"), str) or not gate["reason"].strip():
            raise GateManifestError(f"{gate_id}: reason is required")
        evidence = gate.get("evidence", [])
        blockers = gate.get("blockers", [])
        if not isinstance(evidence, list) or not evidence:
            raise GateManifestError(f"{gate_id}: evidence is required")
        for relative in evidence:
            path = (repo / relative).resolve()
            if repo.resolve() not in path.parents or not path.is_file():
                evidence_errors.append(f"{gate_id}:{relative}:MISSING_OR_OUTSIDE_REPO")
        unknown_blockers = sorted(set(blockers) - blocker_ids)
        if unknown_blockers:
            raise GateManifestError(f"{gate_id}: unknown blockers {unknown_blockers}")
        if state == "EXTERNAL" and not blockers:
            raise GateManifestError(f"{gate_id}: EXTERNAL requires a blocker")
        gate_map[gate_id] = gate

    track_results: dict[str, dict[str, Any]] = {}
    for track_id, track in tracks.items():
        required = track.get("required_gates", [])
        if not required or not all(gate_id in gate_map for gate_id in required):
            raise GateManifestError(f"{track_id}: required_gates are invalid")
        nonpassing = [gate_id for gate_id in required if gate_map[gate_id]["state"] != "PASS"]
        ready = not nonpassing and not evidence_errors
        decision_key = "ready_decision" if ready else "blocked_decision"
        decision = track.get(decision_key)
        if not isinstance(decision, str) or not decision:
            raise GateManifestError(f"{track_id}: {decision_key} is required")
        track_results[track_id] = {
            "ready": ready,
            "decision": decision,
            "nonpassing_gates": nonpassing,
        }

    return {
        "schema_version": manifest["schema_version"],
        "git": {
            "branch": _git(repo, "branch", "--show-current"),
            "head": _git(repo, "rev-parse", "HEAD"),
            "remote_match": _git(repo, "rev-parse", "HEAD")
            == _git(repo, "rev-parse", "origin/main"),
            "working_tree_clean": not bool(_git(repo, "status", "--porcelain")),
        },
        "gate_states": {gate_id: gate["state"] for gate_id, gate in gate_map.items()},
        "evidence_errors": sorted(evidence_errors),
        "tracks": track_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit fail-closed release gates")
    parser.add_argument("--manifest", type=Path, default=Path("config/release-gates.json"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        manifest = json.loads((repo / args.manifest).read_text(encoding="utf-8"))
        report = audit_manifest(manifest, repo=repo)
    except (GateManifestError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["evidence_errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
