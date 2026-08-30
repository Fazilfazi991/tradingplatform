POSITIONING_CASES = (
    "FII buying", "FII selling", "DII offsetting", "persistent flows", "flow reversal",
    "delivery spike", "bulk deal", "block deal", "basis premium", "basis discount",
    "OI expansion", "OI contraction", "rollover", "IV spike", "IV collapse",
    "downside skew", "upside skew", "PCR extreme", "expiry effects", "crowding",
    "flow sentiment contradiction", "flow macro contradiction", "stale option chain",
    "missing strikes", "wrong expiry", "spot timestamp mismatch", "duplicate chain records",
    "zero denominator PCR", "negative OI delta confusion",
    "contract rollover mistaken for new positioning", "corporate-action strike adjustment",
    "illiquid option", "huge bid ask spread", "after-close FII data used intraday",
    "wrong unit", "crore vs contracts confusion", "participant classification ambiguity",
)


def positioning_fixture_cases() -> list[dict[str, str | int]]:
    return [{"fixture_id": f"positioning-{index:03d}", "case": case, "variant": variant,
             "mode": "ENGINEERING_FIXTURE"}
            for index, (case, variant) in enumerate(
                ((case, variant) for case in POSITIONING_CASES for variant in range(7)), start=1)]


def null_positioning_fixture() -> list[dict[str, int | str]]:
    return [{"fixture_id": f"positioning-null-{i:03d}",
             "net_contracts": (-1 if i % 2 else 1) * ((i // 2) % 9),
             "oi_delta": (-1 if i % 2 else 1) * ((i // 2) % 7),
             "mode": "BALANCED_NO_STRUCTURE"} for i in range(250)]
