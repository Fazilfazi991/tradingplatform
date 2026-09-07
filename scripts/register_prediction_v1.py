from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from research_core.prediction_v1 import (
    V1Paths,
    build_registration,
    verify_frozen_dataset,
    write_registration,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal Prediction Engine V1 preregistration")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("research/prediction-v1"))
    args = parser.parse_args()
    paths = V1Paths(args.dataset, args.output)
    manifest = verify_frozen_dataset(paths)
    code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    target = write_registration(paths, build_registration(manifest=manifest, code_sha=code_sha))
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
