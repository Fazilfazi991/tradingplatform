import gzip
import json
from datetime import date

import httpx
import pytest
from verified_edge.providers.base import MarketDataProvider
from verified_edge.providers.upstox import (
    AuthenticationError,
    ProviderSchemaError,
    RateLimitError,
    UpstoxMarketDataProvider,
)


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_provider_interface_conformity():
    assert issubclass(UpstoxMarketDataProvider, MarketDataProvider)


def test_instrument_fixture_parsing_and_mapping():
    payload = [
        {
            "instrument_key": "NSE_EQ|INE1",
            "trading_symbol": "ALPHA",
            "exchange": "NSE",
            "segment": "NSE_EQ",
            "name": "Alpha Ltd",
            "isin": "INE1",
            "instrument_type": "EQUITY",
            "tick_size": 0.05,
        }
    ]
    provider = UpstoxMarketDataProvider(
        token="redacted",
        client=client(
            lambda r: httpx.Response(200, content=gzip.compress(json.dumps(payload).encode()))
        ),
    )
    result = provider.get_instruments()
    assert result[0].symbol == "ALPHA" and provider.resolve_instrument("ALPHA").isin == "INE1"


def test_historical_fixture_parsing():
    body = {"data": {"candles": [["2026-01-02T00:00:00+05:30", 100, 110, 90, 105, 1000, 0]]}}
    provider = UpstoxMarketDataProvider(
        token="redacted",
        base_url="https://example.test",
        client=client(lambda r: httpx.Response(200, json=body)),
    )
    inst = __import__("verified_edge.domain", fromlist=["Instrument"]).Instrument(
        exchange="NSE", segment="NSE_EQ", symbol="ALPHA", provider_instrument_key="NSE_EQ|INE1"
    )
    rows = provider.get_historical_daily(inst, date(2026, 1, 1), date(2026, 1, 2))
    assert rows[0]["close"] == 105


def test_authentication_failure_without_secret():
    provider = UpstoxMarketDataProvider(token=None, client=client(lambda r: httpx.Response(200)))
    provider._token = None
    with pytest.raises(AuthenticationError):
        provider.health_check()


def test_rate_limit_bounded_retries():
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(429)

    provider = UpstoxMarketDataProvider(
        token="redacted", client=client(handler), sleeper=lambda _: None
    )
    with pytest.raises(RateLimitError):
        provider.health_check()
    assert len(attempts) == 3


def test_malformed_provider_payload():
    provider = UpstoxMarketDataProvider(
        token="redacted",
        base_url="https://example.test",
        client=client(lambda r: httpx.Response(200, json={"unexpected": True})),
    )
    inst = __import__("verified_edge.domain", fromlist=["Instrument"]).Instrument(
        exchange="NSE", segment="NSE_EQ", symbol="ALPHA", provider_instrument_key="NSE_EQ|INE1"
    )
    with pytest.raises(ProviderSchemaError):
        provider.get_historical_daily(inst, date(2026, 1, 1), date(2026, 1, 2))
