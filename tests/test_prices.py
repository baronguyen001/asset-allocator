from __future__ import annotations

from pathlib import Path

import responses

from asset_allocator.config import COINGECKO_BASE, STOOQ_BASE
from asset_allocator.models import Holding
from asset_allocator.prices import resolve_price
from asset_allocator.prices.coingecko import spot as crypto_spot
from asset_allocator.prices.stooq import spot as stooq_spot


@responses.activate
def test_stooq_csv_parsing() -> None:
    csv_body = Path("tests/fixtures/stooq_demo.csv").read_text(encoding="utf-8")
    responses.add(responses.GET, STOOQ_BASE, body=csv_body, status=200)
    assert stooq_spot("demo.us") == 11.25


@responses.activate
def test_coingecko_json_parsing() -> None:
    json_body = Path("tests/fixtures/coingecko_demo.json").read_text(encoding="utf-8")
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE}/simple/price",
        body=json_body,
        status=200,
        content_type="application/json",
    )
    assert crypto_spot("demo-coin") == 42.5


@responses.activate
def test_resolve_price_dispatch_and_cache_fallback() -> None:
    json_body = Path("tests/fixtures/coingecko_demo.json").read_text(encoding="utf-8")
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE}/simple/price",
        body=json_body,
        status=200,
        content_type="application/json",
    )
    cache = {}
    price, stale = resolve_price(
        Holding("equity", "Demo Coin", "market", 10, quantity=1, ticker="crypto:demo-coin"),
        cache=cache,
    )
    assert price == 42.5
    assert stale is False
    responses.reset()
    price, stale = resolve_price(
        Holding("equity", "Demo Coin", "market", 10, quantity=1, ticker="crypto:demo-coin"),
        cache=cache,
    )
    assert price == 42.5
    assert stale is True
