from __future__ import annotations

import time
from typing import Any

import requests

from asset_allocator.config import BASE_CCY
from asset_allocator.models import Holding
from asset_allocator.prices import coingecko, stooq
from asset_allocator.prices.base import PriceError, PriceProvider


class _ModuleProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def spot(self, ticker: str) -> float:
        if self.name == "coingecko":
            return coingecko.spot(ticker)
        if self.name == "stooq":
            return stooq.spot(ticker)
        raise PriceError(f"Unknown provider {self.name!r}.")


def get_provider(name: str) -> PriceProvider:
    return _ModuleProvider(name)


def _cache_key(ticker: str) -> str:
    return ticker.lower()


def _read_cached(cache: dict[str, Any], ticker: str, ttl: int) -> tuple[float, bool] | None:
    entry = cache.get(_cache_key(ticker))
    if not isinstance(entry, dict) or "price" not in entry:
        return None
    age = time.time() - float(entry.get("as_of_epoch", 0))
    return float(entry["price"]), age > ttl


def resolve_price(
    holding: Holding,
    *,
    session: requests.Session | None = None,
    cache: dict[str, Any] | None = None,
    ttl: int = 3600,
) -> tuple[float, bool]:
    if not holding.ticker:
        raise PriceError(f"Holding {holding.label!r} has no ticker.")
    ticker = holding.ticker
    cache = cache if cache is not None else {}
    if ttl <= 0:
        cached = _read_cached(cache, ticker, ttl)
        if cached is not None:
            return cached[0], True
    try:
        if ticker.startswith("crypto:"):
            price = coingecko.spot(
                ticker.split(":", 1)[1],
                vs=BASE_CCY.lower(),
                session=session,
            )
        else:
            price = stooq.spot(ticker, session=session)
    except Exception as exc:
        cached = _read_cached(cache, ticker, ttl)
        if cached is not None:
            return cached[0], True
        raise PriceError(f"Could not fetch price for {ticker}: {exc}") from exc
    cache[_cache_key(ticker)] = {"price": price, "as_of_epoch": time.time()}
    return price, False
