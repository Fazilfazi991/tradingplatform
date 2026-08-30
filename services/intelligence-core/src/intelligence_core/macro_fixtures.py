from __future__ import annotations

MACRO_CASES = (
    ("rate hike", "MONETARY_POLICY"),
    ("rate cut", "MONETARY_POLICY"),
    ("inflation upside surprise", "INFLATION"),
    ("GDP beat", "GDP"),
    ("GDP miss", "GDP"),
    ("liquidity injection", "LIQUIDITY"),
    ("INR shock", "CURRENCY"),
    ("crude spike", "COMMODITY"),
    ("crude fall", "COMMODITY"),
    ("US equity selloff", "GLOBAL_EQUITY"),
    ("Asian recovery", "GLOBAL_EQUITY"),
    ("VIX spike", "VOLATILITY"),
    ("yield surge", "GLOBAL_RATE"),
    ("conflicting macro indicators", "OTHER_MACRO"),
    ("revision mistaken for original", "GDP"),
    ("future consensus leakage", "INFLATION"),
    ("ambiguous RBI wording", "MONETARY_POLICY"),
    ("old policy resurfacing", "MONETARY_POLICY"),
    ("headline-only false interpretation", "OTHER_MACRO"),
    ("unit mismatch", "OTHER_MACRO"),
    ("percentage versus basis points", "INTEREST_RATE"),
    ("timezone mistake", "OTHER_MACRO"),
    ("incorrect country", "OTHER_MACRO"),
    ("duplicate macro release", "OTHER_MACRO"),
    ("conflicting sources", "OTHER_MACRO"),
)


def macro_fixture_observations() -> list[dict[str, str | int]]:
    return [
        {
            "fixture_id": f"macro-{index:03d}",
            "case": case,
            "expected_category": category,
            "variant": variant,
        }
        for index, (case, category, variant) in enumerate(
            ((case, category, variant) for case, category in MACRO_CASES for variant in range(6)),
            start=1,
        )
    ]
