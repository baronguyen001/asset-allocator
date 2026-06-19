from __future__ import annotations

import json
from typing import Any

import pytest

from asset_allocator.web import compute_view, create_app, validate_store


def _data() -> dict[str, Any]:
    return {
        "profile": None,
        "target": {
            "profile_name": "custom",
            "weights": {
                "equity": 40,
                "bonds": 10,
                "gold": 10,
                "real_estate": 30,
                "savings": 4,
                "cash": 4,
                "emergency": 2,
            },
        },
        "holdings": [
            {"bucket": "cash", "label": "Cash", "kind": "static", "cost_basis": 50},
            {"bucket": "real_estate", "label": "House", "kind": "static", "cost_basis": 12000},
        ],
        "price_cache": {},
        "history": [],
        "cashflow": [
            {
                "kind": "income",
                "label": "Salary",
                "amount": 80,
                "freq": "monthly",
                "category": "work",
            },
            {
                "kind": "expense",
                "label": "Food",
                "amount": 8,
                "freq": "monthly",
                "category": "living",
            },
            {
                "kind": "expense",
                "label": "Insurance",
                "amount": 60,
                "freq": "yearly",
                "category": "protection",
            },
        ],
        "goals": [
            {"year": 2032, "label": "Freedom", "target": 155000},
            {"year": 2042, "label": "Empire", "target": 1055000},
        ],
    }


def test_compute_view() -> None:
    view = compute_view(_data(), "vi", "VND", 2026)
    assert view["net_worth"] == 12050.0
    assert view["has_budget"] is True
    assert view["budget"]["monthly_income"] == 80.0
    assert all(b["emoji"] for b in view["buckets"])
    assert len(view["goals"]) == 2
    assert view["goals"][0]["year"] == 2032
    assert view["trajectory"]["years"][-1] == 2042
    assert len(view["expense_by_category"]) >= 1


def test_validate_store_ok_and_bad() -> None:
    validate_store(_data())  # should not raise
    with pytest.raises(ValueError):
        validate_store(
            {"holdings": [{"bucket": "bogus", "label": "x", "kind": "static", "cost_basis": 1}]}
        )
    with pytest.raises(ValueError):
        validate_store(
            {"cashflow": [{"kind": "income", "label": "x", "amount": -1, "freq": "monthly"}]}
        )
    with pytest.raises(ValueError):
        validate_store({"goals": [{"year": 2032, "label": "x", "target": 0}]})


def test_app_routes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = tmp_path / "p.json"
    store.write_text(json.dumps(_data()), encoding="utf-8")
    app = create_app(str(store), lang="vi", currency="VND", as_of_year=2026)
    client = app.test_client()

    body = client.get("/").get_data(as_text=True)
    assert "/vendor/chart.js" in body
    assert "Giá trị ròng" in body  # localized strings embedded
    assert "__STATE__" not in body  # placeholder was replaced

    state = client.get("/api/state")
    assert state.status_code == 200
    assert state.get_json()["view"]["net_worth"] == 12050.0

    chart = client.get("/vendor/chart.js")
    assert chart.status_code == 200
    assert len(chart.get_data()) > 50000  # the vendored Chart.js bundle

    payload = _data()
    payload["cashflow"].append(
        {"kind": "expense", "label": "New", "amount": 1, "freq": "monthly", "category": "x"}
    )
    ok = client.post("/api/save", json=payload)
    assert ok.status_code == 200
    assert ok.get_json()["ok"] is True
    assert len(json.loads(store.read_text(encoding="utf-8"))["cashflow"]) == 4

    bad = client.post(
        "/api/save",
        json={"holdings": [{"bucket": "bogus", "label": "x", "kind": "static", "cost_basis": 1}]},
    )
    assert bad.status_code == 400
    assert bad.get_json()["ok"] is False
