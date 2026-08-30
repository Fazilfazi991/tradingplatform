from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from verified_edge.domain import Instrument


class MarketDataProvider(ABC):
    @abstractmethod
    def get_instruments(self) -> list[Instrument]: ...

    @abstractmethod
    def resolve_instrument(self, symbol: str, exchange: str = "NSE") -> Instrument: ...

    @abstractmethod
    def get_historical_daily(
        self, instrument: Instrument, start: date, end: date
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_historical_interval(
        self, instrument: Instrument, unit: str, interval: int, start: date, end: date
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_quote(self, instrument: Instrument) -> dict[str, Any]: ...

    @abstractmethod
    def get_index_data(self, code: str, start: date, end: date) -> list[dict[str, Any]]: ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]: ...

    @abstractmethod
    def provider_metadata(self) -> dict[str, Any]: ...
