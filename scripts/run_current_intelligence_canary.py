from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from intelligence_core.durable import SQLiteOperationsStore
from intelligence_core.forensic_worker import ForensicSemanticProcessor
from intelligence_core.llm_analyzer import (
    AnalyzerTask,
    LLMAnalysisResult,
    OpenAIResponsesAdapter,
    ProviderConfig,
)
from intelligence_core.runtime_forensics import ForensicRuntimeStore
from research_core.common import stable_hash


def load_local_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    workspace = Path.cwd()
    load_local_env(workspace / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "")
    if not api_key or model != "gpt-5.6-luna":
        raise SystemExit("APPROVED_LUNA_CONFIGURATION_REQUIRED")
    config = json.loads(
        (workspace / "config/intelligence-llm-runtime.json").read_text(encoding="utf-8")
    )
    operations = SQLiteOperationsStore(workspace / "data/local/intelligence-operations.sqlite3")
    forensics = ForensicRuntimeStore(workspace / "data/local/intelligence-forensics.sqlite3")
    try:
        events = operations.events()
        if not events:
            raise SystemExit("OBSERVED_EVENT_REQUIRED")
        event = events[-1]
        schema_hash = stable_hash(LLMAnalysisResult.model_json_schema())
        configuration_hash = stable_hash({**config, "model": model})
        processor = ForensicSemanticProcessor(
            store=forensics,
            adapter=OpenAIResponsesAdapter(api_key=api_key),
            provider_config=ProviderConfig(
                provider="openai",
                model=model,
                model_version="runtime-configured",
                enabled=True,
                max_output_tokens=600,
                timeout_seconds=45,
                input_cost_per_million=float(config["input_cost_per_million"]),
                output_cost_per_million=float(config["output_cost_per_million"]),
            ),
            prompt_version=config["prompt_version"],
            schema_version=config["schema_version"],
            schema_hash=schema_hash,
            routing_version=config["routing_version"],
            configuration_hash=configuration_hash,
            retry_policy_version=config["retry_policy_version"],
            grounding_policy_version=config["grounding_policy_version"],
            max_attempts=int(config["max_attempts"]),
            input_price=float(config["input_cost_per_million"]),
            output_price=float(config["output_cost_per_million"]),
        )
        canary_started = datetime.now(UTC)
        canary_id = (
            f"CANARY:{canary_started.strftime('%Y%m%dT%H%M%SZ')}:"
            f"{event.source_id}:{event.source_event_id}"
        )
        result = processor.process(
            event_id=canary_id,
            source_id=event.source_id,
            source_artifact_hash=event.raw_payload_hash,
            title=event.title,
            content=event.summary,
            published_at=event.published_at,
            task=AnalyzerTask.EVENT_CLASSIFICATION,
            now=canary_started,
        )
        attempts = forensics.attempts(result["semantic_request_id"])
        print(
            json.dumps(
                {
                    "state": "CANARY",
                    "excluded_from_live_canonical_event_counts": True,
                    "semantic_request_id": result["semantic_request_id"],
                    "disposition": str(result["disposition"]),
                    "attempts": len(attempts),
                    "transport": [row.transport_status.value for row in attempts],
                    "validation": [row.structured_validation_status.value for row in attempts],
                    "cost_usd": round(sum(row.estimated_total_cost for row in attempts), 8),
                },
                sort_keys=True,
            )
        )
    finally:
        forensics.close()
        operations.close()


if __name__ == "__main__":
    main()
