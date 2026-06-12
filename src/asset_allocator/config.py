"""Configuration defaults for the keyless allocator."""

from __future__ import annotations

import os

ASSET_CLASSES = ["equity", "bonds", "gold", "real_estate", "savings", "cash", "emergency"]

MODEL_TEMPLATES: dict[str, dict[str, float]] = {
    "conservative": {
        "equity": 20,
        "bonds": 35,
        "gold": 10,
        "real_estate": 5,
        "savings": 20,
        "cash": 5,
        "emergency": 5,
    },
    "balanced": {
        "equity": 40,
        "bonds": 25,
        "gold": 10,
        "real_estate": 10,
        "savings": 8,
        "cash": 4,
        "emergency": 3,
    },
    "growth": {
        "equity": 60,
        "bonds": 12,
        "gold": 8,
        "real_estate": 12,
        "savings": 4,
        "cash": 2,
        "emergency": 2,
    },
    "aggressive": {
        "equity": 75,
        "bonds": 5,
        "gold": 5,
        "real_estate": 10,
        "savings": 2,
        "cash": 2,
        "emergency": 1,
    },
}

REBALANCE_BAND = 5.0
STOOQ_BASE = "https://stooq.com/q/d/l/"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

DEFAULT_STORE = os.getenv("ALLOCATOR_STORE", "./portfolio.json")
PRICE_TTL = int(os.getenv("ALLOCATOR_PRICE_TTL", "3600"))
BASE_CCY = os.getenv("ALLOCATOR_BASE_CCY", "USD").upper()
