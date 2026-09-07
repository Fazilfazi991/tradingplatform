from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.live import live_source_handlers, operational_handlers
from intelligence_core.models import IntelligenceRuntimeMode
from intelligence_core.semantic_runtime import configured_semantic_handler
from intelligence_core.worker import IntelligenceWorker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--state", default="data/local/intelligence-operations.sqlite3")
    args = parser.parse_args()
    store = SQLiteOperationsStore(args.state)
    try:
        if args.status:
            print(
                json.dumps(
                    store.service_status(
                        now=datetime.now(UTC), stale_after=timedelta(seconds=30)
                    ),
                    sort_keys=True,
                )
            )
            return
        store.load_config(Path("config/intelligence-schedules.json"), now=datetime.now(UTC))
        store.recover_interrupted(datetime.now(UTC))
        handlers = {**live_source_handlers(store), **operational_handlers(store)}
        handlers["llm-event-analysis"] = configured_semantic_handler(store, workspace=Path.cwd())
        worker = IntelligenceWorker(store, handlers, mode=IntelligenceRuntimeMode.INTERNAL_LIVE)
        if args.once:
            print(worker.run_once())
        else:
            worker.run_forever()
    finally:
        store.close()


if __name__ == "__main__":
    main()
