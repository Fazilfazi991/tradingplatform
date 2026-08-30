from __future__ import annotations

import gzip
import json
import os
import random
import time
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import httpx
from verified_edge.corporate_actions import CorporateAction, CorporateActionType
from verified_edge.domain import Instrument
from verified_edge.providers.base import MarketDataProvider


class ProviderError(RuntimeError):
    pass


class AuthenticationError(ProviderError):
    pass


class RateLimitError(ProviderError):
    pass


class ProviderSchemaError(ProviderError):
    pass


class UpstoxMarketDataProvider(MarketDataProvider):
    INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._token = token or os.getenv("UPSTOX_ACCESS_TOKEN")
        self._base_url = (
            base_url or os.getenv("UPSTOX_BASE_URL") or "https://api.upstox.com"
        ).rstrip("/")
        self._client = client or httpx.Client(timeout=30, follow_redirects=True)
        self._sleep = sleeper
        self._instrument_cache: list[Instrument] | None = None

    def _headers(self) -> dict[str, str]:
        if not self._token:
            raise AuthenticationError("UPSTOX_ACCESS_TOKEN is required for read-only API requests")
        return {"Accept": "application/json", "Authorization": f"Bearer {self._token}"}

    def _request(self, url: str, *, retries: int = 3) -> httpx.Response:
        for attempt in range(1, retries + 1):
            try:
                response = self._client.get(url, headers=self._headers())
            except httpx.TransportError as exc:
                if attempt == retries:
                    raise ProviderError("Upstox network failure after bounded retries") from exc
                self._sleep(min(2 ** (attempt - 1) + random.random() / 10, 8))
                continue
            if response.status_code == 401:
                raise AuthenticationError("Upstox rejected the read-only access token")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == retries:
                    if response.status_code == 429:
                        raise RateLimitError("Upstox rate limit persisted after bounded retries")
                    raise ProviderError(f"Upstox server error {response.status_code}")
                retry_after = response.headers.get("Retry-After")
                delay = (
                    float(retry_after)
                    if retry_after
                    else (2 ** (attempt - 1) + random.random() / 10)
                )
                self._sleep(min(delay, 8))
                continue
            response.raise_for_status()
            return response
        raise AssertionError("unreachable")

    def get_instruments(self) -> list[Instrument]:
        if self._instrument_cache is not None:
            return self._instrument_cache
        response = self._client.get(self.INSTRUMENTS_URL)
        response.raise_for_status()
        try:
            body = (
                gzip.decompress(response.content)
                if response.content[:2] == b"\x1f\x8b"
                else response.content
            )
            records = json.loads(body)
            result = []
            seen: set[str] = set()
            for row in records:
                key = row.get("instrument_key")
                symbol = row.get("trading_symbol")
                if not key or not symbol:
                    continue
                if key in seen:
                    raise ProviderSchemaError(f"duplicate provider instrument key: {key}")
                seen.add(key)
                result.append(
                    Instrument(
                        exchange=row.get("exchange", ""),
                        segment=row.get("segment", ""),
                        symbol=symbol,
                        company_name=row.get("name"),
                        isin=row.get("isin"),
                        instrument_type=row.get("instrument_type", "UNKNOWN"),
                        tick_size=Decimal(str(row["tick_size"]))
                        if row.get("tick_size") is not None
                        else None,
                        provider_instrument_key=key,
                    )
                )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ProviderSchemaError("malformed Upstox instrument payload") from exc
        self._instrument_cache = result
        return result

    def resolve_instrument(self, symbol: str, exchange: str = "NSE") -> Instrument:
        matches = [
            i for i in self.get_instruments() if i.symbol == symbol and i.exchange == exchange
        ]
        if len(matches) != 1:
            raise ProviderError(f"expected one {exchange}:{symbol} mapping, found {len(matches)}")
        return matches[0]

    def get_historical_daily(
        self, instrument: Instrument, start: date, end: date
    ) -> list[dict[str, Any]]:
        return self.get_historical_interval(instrument, "days", 1, start, end)

    def get_historical_interval(
        self, instrument: Instrument, unit: str, interval: int, start: date, end: date
    ) -> list[dict[str, Any]]:
        if not instrument.provider_instrument_key:
            raise ProviderError("instrument has no Upstox provider key")
        encoded = quote(instrument.provider_instrument_key, safe="")
        url = f"{self._base_url}/v3/historical-candle/{encoded}/{unit}/{interval}/{end.isoformat()}/{start.isoformat()}"
        response = self._request(url)
        try:
            candles = response.json()["data"]["candles"]
            return [self._parse_candle(row) for row in candles]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderSchemaError("malformed Upstox candle payload") from exc

    @staticmethod
    def _parse_candle(row: list[Any]) -> dict[str, Any]:
        if len(row) < 6:
            raise ProviderSchemaError("candle requires timestamp, OHLC and volume")
        timestamp = datetime.fromisoformat(str(row[0]))
        return {
            "timestamp": timestamp,
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
            "oi": row[6] if len(row) > 6 else None,
            "provider_row": row,
        }

    def get_quote(self, instrument: Instrument) -> dict[str, Any]:
        if not instrument.provider_instrument_key:
            raise ProviderError("instrument has no Upstox provider key")
        response = self._request(
            f"{self._base_url}/v3/market-quote/ltp?instrument_key={instrument.provider_instrument_key}"
        )
        return response.json()

    def get_corporate_actions(self, isin: str) -> list[CorporateAction]:
        if not isin:
            raise ProviderError("ISIN is required for corporate actions")
        encoded = quote(isin, safe="")
        response = self._request(f"{self._base_url}/v2/fundamentals/{encoded}/corporate-actions")
        try:
            records = response.json()["data"]
            if not isinstance(records, list):
                raise TypeError
            actions = []
            for record in records:
                ratio = str(record.get("ratio") or "").split(":")
                numerator, denominator = (ratio + [None, None])[:2]
                effective = time.strptime(record["expiry_date"], "%d %b %Y")
                actions.append(
                    CorporateAction(
                        action_type=CorporateActionType(str(record["name"]).upper()),
                        effective_date=date(effective.tm_year, effective.tm_mon, effective.tm_mday),
                        source="UPSTOX_FUNDAMENTALS_API",
                        source_version="v2",
                        numerator=Decimal(numerator) if numerator else None,
                        denominator=Decimal(denominator) if denominator else None,
                        cash_amount=Decimal(str(record["amount"]))
                        if record.get("amount") is not None
                        else None,
                        metadata={"event_details": record.get("event_details", [])},
                    )
                )
            return actions
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderSchemaError("malformed Upstox corporate-action payload") from exc

    def get_index_data(self, code: str, start: date, end: date) -> list[dict[str, Any]]:
        instrument = next(
            (i for i in self.get_instruments() if i.provider_instrument_key == code), None
        )
        if instrument is None:
            raise ProviderError(f"index mapping not found: {code}")
        return self.get_historical_daily(instrument, start, end)

    def health_check(self) -> dict[str, Any]:
        started = time.perf_counter()
        response = self._request(f"{self._base_url}/v2/user/profile")
        return {
            "ok": response.status_code == 200,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    def provider_metadata(self) -> dict[str, Any]:
        return {
            "name": "UPSTOX",
            "environment": self._base_url,
            "read_only": True,
            "token_present": bool(self._token),
            "token_value_recorded": False,
        }
