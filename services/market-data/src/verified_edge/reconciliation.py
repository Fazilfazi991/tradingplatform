from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from verified_edge.domain import DailyBar


@dataclass(frozen=True)
class ReconciliationDifference:
    symbol: str
    session_date: str
    field: str
    primary: str
    secondary: str


def reconcile(
    primary: list[DailyBar], secondary: list[DailyBar], price_tolerance: Decimal = Decimal("0.01")
) -> list[ReconciliationDifference]:
    right = {(b.symbol, b.session_date): b for b in secondary}
    differences = []
    for left in primary:
        other = right.get((left.symbol, left.session_date))
        if other is None:
            differences.append(
                ReconciliationDifference(
                    left.symbol, left.session_date.isoformat(), "session", "present", "missing"
                )
            )
            continue
        for field in ("open", "high", "low", "close"):
            a, b = getattr(left, field), getattr(other, field)
            if abs(a - b) > price_tolerance:
                differences.append(
                    ReconciliationDifference(
                        left.symbol, left.session_date.isoformat(), field, str(a), str(b)
                    )
                )
        if left.volume != other.volume:
            differences.append(
                ReconciliationDifference(
                    left.symbol,
                    left.session_date.isoformat(),
                    "volume",
                    str(left.volume),
                    str(other.volume),
                )
            )
    return differences
