FUSION_CASES = (
    "all supportive", "all adverse", "balanced", "technical only", "fundamental only",
    "missing macro", "stale news", "low-quality positive news",
    "strong technical vs strong macro conflict", "positive fundamentals negative guidance",
    "euphoric psychology positive technical", "institutional selling strong fundamentals",
    "news fundamental contradiction", "historical supportive technical adverse",
    "multiple low-quality vs one high-quality", "correlated news psychology macro",
    "one engine available", "two engines available", "three engines available",
    "four engines available", "five engines available", "six engines available",
    "seven engines available", "quality downgrade", "freshness downgrade",
    "orientation change", "contradiction addition", "dependency increase",
    "model disagreement", "regime uncertain", "source conflict", "causal cutoff violation",
)


def fusion_fixture_cases() -> list[dict[str, str | int]]:
    return [{"fixture_id": f"fusion-{index:03d}", "case": case, "variant": variant,
             "mode": "ENGINEERING_FIXTURE"}
            for index, (case, variant) in enumerate(
                ((case, variant) for case in FUSION_CASES for variant in range(10)), start=1)]


def null_fusion_fixture() -> list[dict[str, str | int]]:
    states = ("SUPPORTIVE", "ADVERSE", "NEUTRAL", "MIXED", "UNKNOWN")
    return [{"fixture_id": f"fusion-null-{i:03d}", "orientation": states[i % len(states)],
             "quality_basis_points": i % 7, "mode": "BALANCED_NO_STRUCTURE"} for i in range(300)]
