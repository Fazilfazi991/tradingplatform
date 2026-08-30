from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.models import IntelligenceRuntimeMode
from intelligence_core.worker import IntelligenceWorker


def main() -> None:
    local = Path("data/local")
    local.mkdir(parents=True, exist_ok=True)
    config = local / "soak-schedules.json"
    config.write_text(
        json.dumps(
            {
                "version": "soak-1",
                "timezone": "UTC",
                "jobs": [
                    {
                        "name": "fixture-health-soak",
                        "kind": "INTERVAL",
                        "source_id": "fixture",
                        "cadence_seconds": 5,
                    }
                ],
            }
        )
    )
    state = local / "intelligence-soak.sqlite3"
    store = SQLiteOperationsStore(state)
    started_at = datetime.now(UTC)
    store.load_config(config, now=started_at)
    cycles = []
    worker = IntelligenceWorker(
        store,
        {"fixture-health-soak": lambda job, now: {"health": "HEALTHY", "at": now.isoformat()}},
        mode=IntelligenceRuntimeMode.FIXTURE,
        job_timeout_seconds=5,
    )
    wall_start = time.monotonic()
    while time.monotonic() - wall_start < 31:
        cycles.extend(worker.run_once())
        time.sleep(1)
    elapsed = time.monotonic() - wall_start
    report = {
        "label": "ACTUAL LOCAL FIXTURE SOAK",
        "started_at": started_at.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": elapsed,
        "cycles_completed": len(cycles),
        "cycles": cycles,
        "state_counts": store.counts(),
    }
    target = Path("research/intelligence/local-soak.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    store.close()


if __name__ == "__main__":
    main()
