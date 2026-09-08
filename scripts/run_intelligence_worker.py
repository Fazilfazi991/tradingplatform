from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.live import live_source_handlers, operational_handlers
from intelligence_core.models import IntelligenceRuntimeMode
from intelligence_core.runtime_forensics import ForensicRuntimeStore
from intelligence_core.semantic_runtime import configured_semantic_handler
from intelligence_core.worker import IntelligenceWorker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--state", default="data/local/intelligence-operations.sqlite3")
    parser.add_argument("--output-root", default="data/local/intelligence")
    args = parser.parse_args()
    store = SQLiteOperationsStore(args.state)
    try:
        if args.status:
            health_path = Path("config/intelligence-health.json")
            stale_seconds = 150
            if health_path.exists():
                stale_seconds = int(
                    json.loads(health_path.read_text(encoding="utf-8"))[
                        "heartbeat_stale_seconds"
                    ]
                )
            print(
                json.dumps(
                    store.service_status(
                        now=datetime.now(UTC), stale_after=timedelta(seconds=stale_seconds)
                    ),
                    sort_keys=True,
                )
            )
            return
        if args.stop:
            instance_id = store.request_service_stop()
            if instance_id is None:
                print(json.dumps({"status": "NOT_RUNNING"}))
                return
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                status = store.service_status(
                    now=datetime.now(UTC), stale_after=timedelta(seconds=150)
                )
                if status["status"] == "STOPPED":
                    print(json.dumps({"status": "STOPPED", "instance_id": instance_id}))
                    return
                time.sleep(1)
            raise SystemExit("WORKER_STOP_TIMEOUT")
        store.load_config(Path("config/intelligence-schedules.json"), now=datetime.now(UTC))
        store.recover_interrupted(datetime.now(UTC))
        store.reconcile_completed_missed_runs(now=datetime.now(UTC))
        forensic_path = Path(args.state).with_name("intelligence-forensics.sqlite3")
        forensics = ForensicRuntimeStore(forensic_path)
        try:
            handlers = {
                **live_source_handlers(store, forensics),
                **operational_handlers(store, args.output_root),
            }
            handlers["llm-event-analysis"] = configured_semantic_handler(
                store, workspace=Path.cwd()
            )
            worker = IntelligenceWorker(store, handlers, mode=IntelligenceRuntimeMode.INTERNAL_LIVE)
            if args.once:
                print(worker.run_once())
            else:
                worker.run_forever()
        finally:
            forensics.close()
    finally:
        store.close()


if __name__ == "__main__":
    main()
