from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from asset_allocator.config import DEFAULT_STORE
from asset_allocator.models import Holding


class StoreError(RuntimeError):
    """Raised for friendly persistence errors."""


def load(path: str = DEFAULT_STORE) -> dict[str, Any]:
    store_path = Path(path)
    if not store_path.exists():
        raise StoreError(f"Portfolio store not found: {store_path}")
    try:
        with store_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StoreError(f"Portfolio store is not valid JSON: {store_path}") from exc
    except OSError as exc:
        raise StoreError(f"Could not read portfolio store {store_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise StoreError(f"Portfolio store must contain a JSON object: {store_path}")
    data.setdefault("profile", None)
    data.setdefault("target", None)
    data.setdefault("holdings", [])
    data.setdefault("price_cache", {})
    data.setdefault("history", [])
    data.setdefault("cashflow", [])
    data.setdefault("goals", [])
    return data


def save(data: dict[str, Any], path: str = DEFAULT_STORE) -> None:
    store_path = Path(path)
    try:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except OSError as exc:
        raise StoreError(f"Could not write portfolio store {store_path}: {exc}") from exc


def add_holding(data: dict[str, Any], h: Holding) -> None:
    holdings = data.setdefault("holdings", [])
    if not isinstance(holdings, list):
        raise StoreError("Portfolio store field 'holdings' must be a list.")
    holdings.append(asdict(h))


def remove_holding(data: dict[str, Any], label: str) -> bool:
    holdings = data.setdefault("holdings", [])
    if not isinstance(holdings, list):
        raise StoreError("Portfolio store field 'holdings' must be a list.")
    original = len(holdings)
    data["holdings"] = [holding for holding in holdings if holding.get("label") != label]
    return len(data["holdings"]) != original
