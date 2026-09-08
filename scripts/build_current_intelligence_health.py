from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.current_health import build_current_health, write_current_health
from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.runtime_forensics import ForensicRuntimeStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/local/intelligence-operations.sqlite3")
    parser.add_argument("--forensics", default="data/local/intelligence-forensics.sqlite3")
    parser.add_argument("--output-root", default="data/local/intelligence")
    args = parser.parse_args()
    schedules = json.loads(Path("config/intelligence-schedules.json").read_text(encoding="utf-8"))
    policy = json.loads(Path("config/intelligence-health.json").read_text(encoding="utf-8"))
    lock_path = Path("config/intelligence-runtime-lock.json")
    runtime_lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else None
    store = SQLiteOperationsStore(args.state)
    forensics = ForensicRuntimeStore(Path(args.forensics))
    try:
        report = build_current_health(
            store,
            forensics,
            schedules=schedules,
            policy=policy,
            now=datetime.now(UTC),
            runtime_lock=runtime_lock,
        )
        paths = write_current_health(report, args.output_root)
        print(json.dumps({"status": report["overall_state"], "paths": [str(p) for p in paths]}))
    finally:
        forensics.close()
        store.close()


if __name__ == "__main__":
    main()
