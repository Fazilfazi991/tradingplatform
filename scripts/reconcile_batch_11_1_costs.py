from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from intelligence_core.soak_operations import aggregate_costs, make_cost_entry

INPUT_PRICE = 0.20
OUTPUT_PRICE = 1.20


def main() -> None:
    health = json.loads(Path("research/intelligence/openai-health.json").read_text(encoding="utf-8"))
    validation = json.loads(
        Path("research/intelligence/live-llm-validation.json").read_text(encoding="utf-8")
    )
    occurred_at = datetime.fromisoformat(validation["generated_at"])
    entries = [
        make_cost_entry(
            occurred_at=occurred_at,
            provider="openai",
            model=health["model"],
            task="HEALTH_CHECK",
            source_id="provider-health",
            canonical_event_id="batch-11.1-health",
            input_tokens=int(health["input_tokens"]),
            output_tokens=int(health["output_tokens"]),
            cache_hit=False,
            latency_ms=0,
            input_price_per_million=INPUT_PRICE,
            output_price_per_million=OUTPUT_PRICE,
        )
    ]
    for row in validation["rows"]:
        entries.append(
            make_cost_entry(
                occurred_at=occurred_at,
                provider="openai",
                model=validation["model"],
                task=(
                    "RBI_POLICY_INTERPRETATION"
                    if row["source"] == "rbi-press-releases-rss"
                    else "EVENT_CLASSIFICATION"
                ),
                source_id=row["source"],
                canonical_event_id=row["case_id"],
                input_tokens=int(row["input_tokens"]),
                output_tokens=int(row["output_tokens"]),
                cache_hit=False,
                latency_ms=float(row["latency_ms"]),
                input_price_per_million=INPUT_PRICE,
                output_price_per_million=OUTPUT_PRICE,
            )
        )
    cached = validation["rows"][0]
    entries.append(
        make_cost_entry(
            occurred_at=occurred_at,
            provider="openai",
            model=validation["model"],
            task="EVENT_CLASSIFICATION",
            source_id=cached["source"],
            canonical_event_id=cached["case_id"],
            input_tokens=int(cached["input_tokens"]),
            output_tokens=int(cached["output_tokens"]),
            cache_hit=True,
            latency_ms=0,
            input_price_per_million=0,
            output_price_per_million=0,
        )
    )
    totals = aggregate_costs(entries)
    report = {
        "root_cause": (
            "The $0.004098 value was the entire 13-call validation run, not fixture-only cost. "
            "RBI and SEBI were subsets of that total and were accidentally presented as additive. "
            "The separate health call was omitted. The application-cache replay made no provider call."
        ),
        "pricing_usd_per_million": {"input": INPUT_PRICE, "output": OUTPUT_PRICE},
        "session_total_including_health_usd": totals["total_cost_usd"],
        "validation_total_usd": validation["estimated_cost_usd"],
        "health_call_cost_usd": entries[0].total_cost_usd,
        "ledger": [entry.model_dump(mode="json") for entry in entries],
        "aggregates": totals,
    }
    target = Path("research/intelligence/batch-11.1-cost-reconciliation.json")
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "ledger"}, sort_keys=True))


if __name__ == "__main__":
    main()
