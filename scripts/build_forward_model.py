from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from research_core.forward_model import fit_frozen_forward_model
from research_core.forward_runtime import FrozenForwardPackage
from research_core.prediction_v1 import V1Paths, atomic_json, verify_frozen_dataset


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_once(path: Path, payload: dict[str, Any], *, hash_field: str) -> None:
    if path.exists():
        existing = read(path)
        if existing.get(hash_field) != payload.get(hash_field):
            raise RuntimeError(f"refusing to replace different frozen artifact: {path}")
        return
    atomic_json(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the disabled Prediction V1 forward package")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--research", type=Path, default=Path("research/prediction-v1"))
    parser.add_argument(
        "--frame-cache", type=Path, default=Path("data/local/prediction-v1/frame.parquet")
    )
    parser.add_argument(
        "--artifact", type=Path, default=Path("research/prediction-v1/forward-model-v1.json")
    )
    parser.add_argument(
        "--package", type=Path, default=Path("research/prediction-v1/forward-package-v1.json")
    )
    args = parser.parse_args()
    paths = V1Paths(args.dataset, args.research)
    manifest = verify_frozen_dataset(paths)
    if not args.frame_cache.is_file():
        raise SystemExit("FROZEN_FRAME_CACHE_REQUIRED")
    import pandas as pd

    frame = pd.read_parquet(args.frame_cache)
    code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    registration = read(args.research / "prediction-v1-registration.json")
    decision = read(args.research / "prediction-v1-pre-holdout-decision.json")
    holdout = read(args.research / "prediction-v1-holdout-report.json")
    artifact = fit_frozen_forward_model(
        frame,
        dataset_hash=manifest["dataset_hash"],
        registration=registration,
        decision=decision,
        holdout_report=holdout,
        source_manifest_created_at=manifest["created_at"],
        code_sha=code_sha,
    )
    package = FrozenForwardPackage(
        approved=False,
        dataset_hash=artifact.dataset_hash,
        model_hash=artifact.artifact_hash,
        feature_config_hash=artifact.feature_config_hash,
        registration_hash=artifact.registration_hash,
        holdout_report_hash=artifact.holdout_report_hash,
        horizons=tuple(model.horizon for model in artifact.models),
        created_at=artifact.source_manifest_created_at,
        code_sha=artifact.build_code_sha,
    )
    write_once(args.artifact, artifact.model_dump(mode="json"), hash_field="artifact_hash")
    write_once(args.package, package.model_dump(mode="json"), hash_field="package_hash")
    print(
        json.dumps(
            {
                "artifact_hash": artifact.artifact_hash,
                "feature_config_hash": artifact.feature_config_hash,
                "package_hash": package.package_hash,
                "approved": package.approved,
                "enabled": False,
                "forward_predictions_started": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
