from __future__ import annotations

import pytest

from asset_allocator.contribute import plan_contribution
from asset_allocator.models import BucketStatus, PortfolioStatus


def _status() -> PortfolioStatus:
    # Total 1000: equity underweight (40 vs 60 target), bonds overweight (60 vs 40 target).
    return PortfolioStatus(
        as_of="2026-06-12T00:00:00+00:00",
        base_ccy="USD",
        total_value=1000.0,
        total_cost=1000.0,
        total_pnl=0.0,
        total_pnl_pct=0.0,
        stale_prices=[],
        buckets=[
            BucketStatus("equity", 400.0, 400.0, 0.0, 0.0, 40.0, 60.0, -20.0),
            BucketStatus("bonds", 600.0, 600.0, 0.0, 0.0, 60.0, 40.0, 20.0),
        ],
    )


def test_contribution_sums_to_amount_exactly() -> None:
    items = plan_contribution(_status(), 200.0)
    assert round(sum(item.amount for item in items), 2) == 200.0


def test_contribution_is_buy_only_and_fills_underweight_first() -> None:
    items = plan_contribution(_status(), 200.0)
    by_bucket = {item.bucket: item for item in items}
    assert all(item.amount >= 0.0 for item in items)
    # New total 1200; equity target 60% -> 720 (deficit 320), bonds 40% -> 480 (no deficit).
    # 200 <= total deficit 320, so the whole contribution goes to equity.
    assert by_bucket["equity"].amount == 200.0
    assert by_bucket["bonds"].amount == 0.0


def test_contribution_overflow_spreads_remainder_by_target() -> None:
    items = plan_contribution(_status(), 1000.0)
    by_bucket = {item.bucket: item for item in items}
    assert round(sum(item.amount for item in items), 2) == 1000.0
    assert by_bucket["equity"].amount > by_bucket["bonds"].amount


def test_projected_weights_move_toward_target() -> None:
    items = plan_contribution(_status(), 320.0)
    equity = next(item for item in items if item.bucket == "equity")
    assert equity.current_weight < equity.projected_weight <= equity.target_weight + 0.01


def test_zero_amount_is_all_zero() -> None:
    items = plan_contribution(_status(), 0.0)
    assert all(item.amount == 0.0 for item in items)


def test_negative_amount_raises() -> None:
    with pytest.raises(ValueError):
        plan_contribution(_status(), -10.0)


def test_no_target_weights_still_balances_to_amount() -> None:
    status = PortfolioStatus(
        as_of="2026-06-12T00:00:00+00:00",
        base_ccy="USD",
        total_value=500.0,
        total_cost=500.0,
        total_pnl=0.0,
        total_pnl_pct=0.0,
        stale_prices=[],
        buckets=[BucketStatus("equity", 500.0, 500.0, 0.0, 0.0, 100.0, 0.0, 100.0)],
    )
    items = plan_contribution(status, 100.0)
    assert round(sum(item.amount for item in items), 2) == 100.0
