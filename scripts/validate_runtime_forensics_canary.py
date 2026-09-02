from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from intelligence_core.forensic_worker import ForensicSemanticProcessor
from intelligence_core.llm_analyzer import (
    AnalyzerTask,
    LLMAnalysisResult,
    OpenAIResponsesAdapter,
    ProviderConfig,
)
from intelligence_core.runtime_forensics import ForensicRuntimeStore, TerminalDisposition
from research_core.common import stable_hash

INPUT_PRICE, OUTPUT_PRICE = 0.20, 1.20
PROMPT_VERSION = "event-intelligence-v1-forensic-canary-v2-production-path"
SCHEMA_VERSION = "llm-analysis-result-v1"
RETRY_POLICY_VERSION = "structured-bounded-v1"


def load_env(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def observed_cases(path: Path, *, limit: int = 50) -> list[dict[str, Any]]:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT payload_json FROM information_events ORDER BY observed_at LIMIT ?", (limit,)
        )
        return [json.loads(row[0]) for row in rows]
    finally:
        connection.close()


def main() -> None:
    workspace = Path.cwd()
    load_env(workspace / ".env")
    api_key, model = os.environ.get("OPENAI_API_KEY", ""), os.environ.get("OPENAI_MODEL", "")
    if not api_key or model != "gpt-5.6-luna":
        raise SystemExit("LIVE_LUNA_CONFIGURATION_REQUIRED")
    cases = observed_cases(workspace / "data/local/24h-live-intelligence-soak.sqlite3")
    if len(cases) < 50:
        raise SystemExit("FIFTY_OBSERVED_CASES_REQUIRED")
    database = workspace / "data/local/runtime-forensics-canary.sqlite3"
    if database.exists():
        database.unlink()
    store = ForensicRuntimeStore(database)
    schema_hash = stable_hash(LLMAnalysisResult.model_json_schema())
    processor = ForensicSemanticProcessor(
        store=store,
        adapter=OpenAIResponsesAdapter(api_key=api_key),
        provider_config=ProviderConfig(
            provider="openai",
            model=model,
            model_version="runtime-frozen",
            enabled=True,
            max_output_tokens=600,
            timeout_seconds=45,
        ),
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        schema_hash=schema_hash,
        routing_version="openai-primary-v1",
        configuration_hash=stable_hash(
            {"prompt": PROMPT_VERSION, "schema": schema_hash, "retry": RETRY_POLICY_VERSION}
        ),
        retry_policy_version=RETRY_POLICY_VERSION,
    )
    outcomes: Counter[str] = Counter()
    for case in cases:
        outcome = processor.process(
            event_id=f"{case['source_id']}:{case['source_event_id']}",
            source_id=case["source_id"],
            source_artifact_hash=case["raw_payload_hash"],
            title=case["title"],
            content=case["summary"],
            published_at=datetime.fromisoformat(case["published_at"])
            if case.get("published_at")
            else None,
            task=AnalyzerTask.RBI_POLICY_INTERPRETATION
            if case["source_id"].startswith("rbi")
            else AnalyzerTask.EVENT_CLASSIFICATION,
        )
        outcomes[str(outcome["disposition"])] += 1
    report = store.reconciliation()
    report.update(
        {
            "cases": len(cases),
            "outcomes": dict(outcomes),
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "production_processor": f"{ForensicSemanticProcessor.__module__}.{ForensicSemanticProcessor.__name__}",
            "pass": report["semantic_requests"] == 50
            and report["attempts"] >= 50
            and report["transport_health"] != "UNAVAILABLE"
            and sum(
                report["event_dispositions"].get(value.value, 0) for value in TerminalDisposition
            )
            == 50,
        }
    )
    target = workspace / "research/intelligence/runtime-forensics-canary.json"
    target.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, default=str))
    store.close()


if __name__ == "__main__":
    main()
