from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def put_json(self, relative_path: str, value: Any, *, immutable: bool = True) -> str:
        target = self.root / relative_path
        if immutable and target.exists():
            raise FileExistsError(f"immutable artifact already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":"), default=str), encoding="utf-8"
        )
        return target.as_posix()

    def get_json(self, relative_path: str) -> Any:
        return json.loads((self.root / relative_path).read_text(encoding="utf-8"))
