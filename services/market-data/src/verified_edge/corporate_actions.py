from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from verified_edge.domain import DailyBar


class CorporateActionType(StrEnum):
    SPLIT = "SPLIT"
    BONUS = "BONUS"
    DIVIDEND = "DIVIDEND"
    RIGHTS = "RIGHTS"
    MERGER = "MERGER"
    DEMERGER = "DEMERGER"
    SYMBOL_CHANGE = "SYMBOL_CHANGE"
    CAPITAL_CHANGE = "CAPITAL_CHANGE"


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True)
    action_type: CorporateActionType
    effective_date: date
    source: str
    source_version: str
    numerator: Decimal | None = None
    denominator: Decimal | None = None
    cash_amount: Decimal | None = None
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def valid_terms(self) -> CorporateAction:
        if self.action_type in {CorporateActionType.SPLIT, CorporateActionType.BONUS}:
            if not self.numerator or not self.denominator:
                raise ValueError("split/bonus action requires positive numerator and denominator")
            if self.numerator <= 0 or self.denominator <= 0:
                raise ValueError("corporate-action ratio must be positive")
        if self.action_type == CorporateActionType.DIVIDEND and (
            self.cash_amount is None or self.cash_amount < 0
        ):
            raise ValueError("dividend requires a non-negative cash amount")
        return self


class AdjustmentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    session_date: date
    action: CorporateActionType
    effective_date: date
    price_factor: Decimal
    volume_factor: Decimal
    source: str
    source_version: str
    calculation: str


def adjustment_factor(action: CorporateAction) -> tuple[Decimal, Decimal]:
    if action.action_type in {CorporateActionType.SPLIT, CorporateActionType.BONUS}:
        assert action.numerator is not None and action.denominator is not None
        return action.denominator / action.numerator, action.numerator / action.denominator
    raise ValueError(f"{action.action_type} requires a reference price or explicit vendor factor")


def adjust_bars(
    raw: list[DailyBar], actions: list[CorporateAction]
) -> tuple[list[DailyBar], list[AdjustmentRecord]]:
    """Return a separate adjusted series; raw inputs remain immutable and unchanged."""
    adjusted = []
    ledger = []
    for bar in raw:
        price_factor = Decimal(1)
        volume_factor = Decimal(1)
        applicable = [action for action in actions if bar.session_date < action.effective_date]
        for action in applicable:
            price, volume = adjustment_factor(action)
            price_factor *= price
            volume_factor *= volume
            ledger.append(
                AdjustmentRecord(
                    session_date=bar.session_date,
                    action=action.action_type,
                    effective_date=action.effective_date,
                    price_factor=price,
                    volume_factor=volume,
                    source=action.source,
                    source_version=action.source_version,
                    calculation=f"price*{price};volume*{volume}",
                )
            )
        adjusted.append(
            bar.model_copy(
                update={
                    "open": bar.open * price_factor,
                    "high": bar.high * price_factor,
                    "low": bar.low * price_factor,
                    "close": bar.close * price_factor,
                    "volume": int(Decimal(bar.volume) * volume_factor),
                    "canonical_version": bar.canonical_version + 1,
                    "transformation_hash": f"adjusted:{bar.transformation_hash}",
                }
            )
        )
    return adjusted, ledger
