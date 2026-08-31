from __future__ import annotations

SCENARIOS = (
    "duplicate news", "same story many websites", "primary source found",
    "primary source contradicts media", "unknown entity", "multiple entities",
    "stale story", "recycled story", "source-rights ambiguity", "collector failure",
    "browser failure", "prompt injection", "false primary-source match", "changed filing",
    "rumour then denial", "missed scheduled run", "new official filing", "material update",
    "newly confirmed event", "newly contradicted event",
)


def research_operator_scenarios() -> list[dict[str, str | int]]:
    return [
        {
            "scenario_id": f"codex-research-{index:03d}",
            "scenario": scenario,
            "variant": variant,
            "expected_authority": "RESEARCH_CANDIDATE_ONLY",
            "expected_prediction_state": "UNCHANGED",
        }
        for index, (scenario, variant) in enumerate(
            ((scenario, variant) for scenario in SCENARIOS for variant in range(5)), start=1
        )
    ]
