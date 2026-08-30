FUNDAMENTAL_CASES = (
    "strong growth", "revenue slowdown", "margin expansion", "margin compression",
    "cash-flow divergence", "debt increase", "debt reduction", "receivable stress",
    "inventory build", "positive guidance", "guidance cut", "large one-off income",
    "dilution", "buyback", "restatement", "bank results", "conglomerate segments",
    "commodity-sensitive business", "wrong reporting period", "unit mismatch",
    "standalone vs consolidated confusion", "restated vs original values", "TTM misuse",
    "quarter vs annual comparison", "negative number shown in parentheses",
    "crore vs million", "currency mismatch", "one-off item treated as recurring",
    "EPS split adjustment error", "future filing leakage", "duplicate filing",
    "LLM invented number",
)


def fundamental_fixture_cases() -> list[dict[str, str | int]]:
    return [
        {"fixture_id": f"fundamental-{index:03d}", "case": case, "variant": variant,
         "mode": "ENGINEERING_FIXTURE"}
        for index, (case, variant) in enumerate(
            ((case, variant) for case in FUNDAMENTAL_CASES for variant in range(5)), start=1
        )
    ]
