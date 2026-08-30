from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from statistics import median

from verified_edge.domain import DailyBar


class ReconciliationClass(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    ROUNDING_VARIANCE = "ROUNDING_VARIANCE"
    EXPLAINED_ADJUSTMENT = "EXPLAINED_ADJUSTMENT"
    SOURCE_CORRECTION = "SOURCE_CORRECTION"
    UNEXPLAINED_CONFLICT = "UNEXPLAINED_CONFLICT"


@dataclass(frozen=True)
class ReconciliationDifference:
    symbol: str
    session_date: str
    field: str
    primary: str
    secondary: str
    classification: ReconciliationClass = ReconciliationClass.UNEXPLAINED_CONFLICT


@dataclass(frozen=True)
class ReconciliationReport:
    comparable_rows: int
    exact_matches: int
    price_mismatches: int
    volume_mismatches: int
    missing_primary: int
    missing_secondary: int
    median_price_delta: Decimal
    p95_price_delta: Decimal
    max_price_delta: Decimal
    differences: tuple[ReconciliationDifference, ...]


def reconciliation_report(
    primary: list[DailyBar], secondary: list[DailyBar], price_tolerance: Decimal = Decimal("0.01")
) -> ReconciliationReport:
    left = {(bar.symbol, bar.session_date): bar for bar in primary}
    right = {(bar.symbol, bar.session_date): bar for bar in secondary}
    shared = sorted(set(left) & set(right), key=lambda key: (key[0], key[1]))
    differences = []
    exact = price_mismatches = volume_mismatches = 0
    deltas: list[Decimal] = []
    for key in shared:
        a, b = left[key], right[key]
        row_exact = True
        for field in ("open", "high", "low", "close"):
            delta = abs(getattr(a, field) - getattr(b, field))
            deltas.append(delta)
            if delta > price_tolerance:
                row_exact = False
                price_mismatches += 1
                differences.append(
                    ReconciliationDifference(
                        a.symbol,
                        a.session_date.isoformat(),
                        field,
                        str(getattr(a, field)),
                        str(getattr(b, field)),
                    )
                )
        if a.volume != b.volume:
            row_exact = False
            volume_mismatches += 1
            differences.append(
                ReconciliationDifference(
                    a.symbol, a.session_date.isoformat(), "volume", str(a.volume), str(b.volume)
                )
            )
        exact += row_exact
    for key in sorted(set(left) - set(right), key=lambda item: (item[0], item[1])):
        item = left[key]
        differences.append(
            ReconciliationDifference(
                item.symbol, item.session_date.isoformat(), "session", "present", "missing"
            )
        )
    for key in sorted(set(right) - set(left), key=lambda item: (item[0], item[1])):
        item = right[key]
        differences.append(
            ReconciliationDifference(
                item.symbol, item.session_date.isoformat(), "session", "missing", "present"
            )
        )
    ordered = sorted(deltas)
    p95 = ordered[max(0, int(len(ordered) * Decimal("0.95")) - 1)] if ordered else Decimal(0)
    return ReconciliationReport(
        comparable_rows=len(shared),
        exact_matches=exact,
        price_mismatches=price_mismatches,
        volume_mismatches=volume_mismatches,
        missing_primary=len(set(right) - set(left)),
        missing_secondary=len(set(left) - set(right)),
        median_price_delta=median(deltas) if deltas else Decimal(0),
        p95_price_delta=p95,
        max_price_delta=max(deltas, default=Decimal(0)),
        differences=tuple(differences),
    )


def reconcile(
    primary: list[DailyBar], secondary: list[DailyBar], price_tolerance: Decimal = Decimal("0.01")
) -> list[ReconciliationDifference]:
    return list(reconciliation_report(primary, secondary, price_tolerance).differences)
