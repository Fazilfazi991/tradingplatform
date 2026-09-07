from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from research_core.forward_runtime import ForwardMarketObservation, ForwardPaperRuntime
from research_core.forward_validation import ForwardPrediction, ForwardValidationLedger


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("version") != "1" or config.get("public_delivery") != "BLOCKED":
        raise ValueError("invalid forward-paper configuration")
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description="Internal forward-paper ledger operation")
    parser.add_argument("--config", type=Path, default=Path("config/forward-paper.json"))
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--issue", type=Path, metavar="PREDICTIONS_JSON")
    actions.add_argument("--resolve", type=Path, metavar="OBSERVATIONS_JSON")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.status:
        print(
            json.dumps(
                {
                    "enabled": bool(config.get("enabled")),
                    "public_delivery": "BLOCKED",
                    "research_state": config.get("research_state"),
                    "package_configured": bool(config.get("package_path")),
                },
                sort_keys=True,
            )
        )
        return 0
    if not config.get("enabled"):
        raise SystemExit("FORWARD_PAPER_DISABLED")
    package_path = config.get("package_path")
    if not isinstance(package_path, str) or not package_path:
        raise SystemExit("FORWARD_PACKAGE_NOT_CONFIGURED")
    ledger_path = Path(config["ledger_path"])
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = ForwardValidationLedger(ledger_path)
    try:
        runtime = ForwardPaperRuntime.from_package_file(ledger, package_path)
        now = datetime.now(UTC)
        if args.issue:
            payload = json.loads(args.issue.read_text(encoding="utf-8"))
            runtime.issue_batch(
                [ForwardPrediction.model_validate(item) for item in payload], now=now
            )
        elif args.resolve:
            payload = json.loads(args.resolve.read_text(encoding="utf-8"))
            for item in payload:
                runtime.resolve_observation(
                    ForwardMarketObservation.model_validate(item), now=now
                )
        report = ledger.report()
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
            )
        print(json.dumps(report, sort_keys=True))
        return 0
    finally:
        ledger.close()


if __name__ == "__main__":
    raise SystemExit(main())
