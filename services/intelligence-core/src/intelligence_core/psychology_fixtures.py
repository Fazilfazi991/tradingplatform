PSYCHOLOGY_CASES = (
    "gradual optimism", "rapid positive narrative", "panic-like news surge", "rumour frenzy",
    "confirmed negative event", "mixed narrative", "attention spike without sentiment",
    "low-attention strong sentiment", "crowded positive narrative", "narrative reversal",
    "macro fear", "sector optimism", "management optimism contradicted by results",
    "regulatory uncertainty", "sarcasm", "negation", "clickbait", "old story resurfaced",
    "bot-like repetitive stories", "duplicate syndication", "rumour repeated as fact",
    "positive headline with negative body", "negative headline with positive body",
    "ambiguous company alias", "multi-company story", "prompt injection", "LLM disagreement",
)


def psychology_fixture_cases() -> list[dict[str, str | int]]:
    return [
        {"fixture_id": f"psychology-{index:03d}", "case": case, "variant": variant,
         "mode": "ENGINEERING_FIXTURE"}
        for index, (case, variant) in enumerate(
            ((case, variant) for case in PSYCHOLOGY_CASES for variant in range(8)), start=1)
    ]


def null_psychology_fixture() -> list[dict[str, str | int]]:
    directions = ("POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED")
    return [{"fixture_id": f"psychology-null-{index:03d}",
             "direction": directions[index % len(directions)], "strength_basis_points": index % 11,
             "mode": "DETERMINISTIC_RANDOM_NO_STRUCTURE"} for index in range(200)]
