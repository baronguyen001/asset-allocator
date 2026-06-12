from __future__ import annotations

import csv
from io import StringIO

import requests

from asset_allocator.config import STOOQ_BASE
from asset_allocator.prices.base import PriceError


def spot(ticker: str, *, session: requests.Session | None = None) -> float:
    client = session or requests.Session()
    response = client.get(STOOQ_BASE, params={"s": ticker, "i": "d"}, timeout=10)
    response.raise_for_status()
    rows = list(csv.DictReader(StringIO(response.text)))
    if not rows:
        raise PriceError(f"No Stooq rows returned for {ticker}.")
    close = rows[-1].get("Close", "")
    if close in {"", "N/D", None}:
        raise PriceError(f"No Stooq close price returned for {ticker}.")
    try:
        price = float(close)
    except ValueError as exc:
        raise PriceError(f"Invalid Stooq close price for {ticker}: {close}") from exc
    if price <= 0:
        raise PriceError(f"Non-positive Stooq close price for {ticker}.")
    return price
