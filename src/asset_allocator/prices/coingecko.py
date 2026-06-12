from __future__ import annotations

import requests

from asset_allocator.config import COINGECKO_BASE
from asset_allocator.prices.base import PriceError


def spot(coin_id: str, *, vs: str = "usd", session: requests.Session | None = None) -> float:
    client = session or requests.Session()
    url = f"{COINGECKO_BASE}/simple/price"
    response = client.get(url, params={"ids": coin_id, "vs_currencies": vs}, timeout=10)
    response.raise_for_status()
    payload = response.json()
    try:
        price = float(payload[coin_id][vs])
    except (KeyError, TypeError, ValueError) as exc:
        raise PriceError(f"No CoinGecko spot price returned for {coin_id}.") from exc
    if price <= 0:
        raise PriceError(f"Non-positive CoinGecko spot price for {coin_id}.")
    return price
