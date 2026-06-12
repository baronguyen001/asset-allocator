from __future__ import annotations

import pytest

from asset_allocator.models import Holding
from asset_allocator.store import StoreError, add_holding, load, remove_holding, save


def test_round_trip_save_load_add_remove(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "portfolio.json"
    data = {"profile": None, "target": None, "holdings": [], "price_cache": {}}
    add_holding(data, Holding("cash", "Demo Cash", "static", 100))
    save(data, str(path))
    loaded = load(str(path))
    assert loaded["holdings"][0]["label"] == "Demo Cash"
    assert remove_holding(loaded, "Demo Cash") is True
    assert loaded["holdings"] == []


def test_corrupt_file_has_friendly_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "portfolio.json"
    path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(StoreError, match="not valid JSON"):
        load(str(path))
