from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.live import live_source_handlers, operational_handlers
from intelligence_core.models import IntelligenceRuntimeMode
from intelligence_core.worker import IntelligenceWorker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state", default="data/local/intelligence-operations.sqlite3")
    args = parser.parse_args()
    store = SQLiteOperationsStore(args.state)
    store.load_config(Path("config/intelligence-schedules.json"), now=datetime.now(UTC))
    store.recover_interrupted(datetime.now(UTC))
    handlers = {**live_source_handlers(store), **operational_handlers(store)}
    worker = IntelligenceWorker(store, handlers, mode=IntelligenceRuntimeMode.INTERNAL_LIVE)
    if args.once:
        print(worker.run_once())
    else:
        worker.run_forever()


if __name__ == "__main__":
    main()
