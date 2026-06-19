from __future__ import annotations

import pytest

from asset_allocator.allocation import (
    custom_allocation,
    rebalance,
    split_amount,
    target_allocation,
)
from asset_allocator.config import MODEL_TEMPLATES
from asset_allocator.models import BucketStatus, PortfolioStatus, RiskProfile


def test_custom_allocation_normalises_to_100() -> None:
    target = custom_allocation({"equity": 50, "bonds": 30, "gold": 20})
    assert target.profile_name == "custom"
    assert sum(target.weights.values()) == pytest.approx(100.0)
    assert target.weights["equity"] == pytest.approx(50.0)
    assert target.weights["cash"] == 0.0


def test_custom_allocation_rejects_negative() -> None:
    with pytest.raises(ValueError):
        custom_allocation({"equity": -10, "bonds": 110})


def test_template_weights_sum_to_100() -> None:
    for weights in MODEL_TEMPLATES.values():
        assert sum(weights.values()) == 100


def test_glide_path_tilts_equity_and_normalises() -> None:
    profile = RiskProfile(name="balanced", score=54, horizon_years=8, age=60)
    target = target_allocation(profile, glide_path=True)
    assert target.weights["equity"] == pytest.approx(50.0)
    assert sum(target.weights.values()) == pytest.approx(100.0)


def test_split_amount_sums_to_total(balanced_target) -> None:  # type: ignore[no-untyped-def]
    split = split_amount(balanced_target, 100000)
    assert sum(split.values()) == 100000
    assert split["equity"] == 40000


def test_rebalance_band_logic() -> None:
    status = PortfolioStatus(
        as_of="2026-06-12T00:00:00+00:00",
        base_ccy="USD",
        total_value=1000,
        total_cost=1000,
        total_pnl=0,
        total_pnl_pct=0,
        stale_prices=[],
        buckets=[
            BucketStatus("equity", 550, 500, 50, 10, 55, 40, 15),
            BucketStatus("bonds", 200, 250, -50, -20, 20, 25, -5),
            BucketStatus("cash", 250, 250, 0, 0, 25, 35, -10),
        ],
    )
    actions = rebalance(status, band=5)
    assert actions[0].direction == "sell"
    assert actions[0].amount == 150
    assert actions[1].direction == "hold"
    assert actions[2].direction == "buy"
