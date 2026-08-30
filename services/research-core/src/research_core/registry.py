from __future__ import annotations

import json
from pathlib import Path

from research_core.common import file_hash
from research_core.objects import PredictionExperiment


class DuplicateExperimentError(FileExistsError):
    pass


class ExperimentRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def register(self, experiment: PredictionExperiment) -> Path:
        matches = list(self.root.glob(f"*--{experiment.config_hash}.json"))
        if matches:
            raise DuplicateExperimentError(
                f"experiment config already registered: {matches[0].name}"
            )
        path = self.root / f"{experiment.experiment_id}--{experiment.config_hash}.json"
        path.write_text(
            json.dumps(experiment.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def write_result(self, experiment: PredictionExperiment, result: dict) -> tuple[Path, str]:
        path = self.root / f"{experiment.experiment_id}--result.json"
        if path.exists():
            raise DuplicateExperimentError(f"experiment result is immutable: {path.name}")
        path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return path, file_hash(path)
