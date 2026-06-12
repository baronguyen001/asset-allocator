from __future__ import annotations

from asset_allocator.models import Holding
from asset_allocator.valuation import holding_value, revalue


def test_holding_value_market_accrual_static(as_of: str) -> None:
    assert (
        holding_value(
            Holding("equity", "Demo", "market", 100, quantity=2),
            as_of=as_of,
            price=60,
        )
        == 120
    )
    accrual = holding_value(
        Holding("savings", "Demo", "accrual", 1000, apy=12, opened="2025-06-12"),
        as_of=as_of,
        price=None,
    )
    assert 1119 < accrual < 1121
    assert holding_value(Holding("cash", "Demo", "static", 500), as_of=as_of, price=None) == 500


def test_revalue_uses_cached_prices_offline_and_collects_stale(
    as_of: str,
    balanced_target,  # type: ignore[no-untyped-def]
) -> None:
    holdings = [
        Holding("equity", "Demo Equity", "market", 100, quantity=2, ticker="demo.us"),
        Holding("cash", "Demo Cash", "static", 50),
    ]
    cache = {"demo.us": {"price": 60, "as_of_epoch": 0}}
    status = revalue(holdings, balanced_target, as_of=as_of, refresh=False, cache=cache)
    assert status.total_value == 170
    assert status.stale_prices == ["demo.us"]
    assert status.buckets[0].market_value == 120


def test_revalue_never_crashes_on_one_bad_ticker(as_of: str, balanced_target) -> None:  # type: ignore[no-untyped-def]
    holdings = [Holding("equity", "Bad Demo", "market", 100, quantity=2, ticker="missing.us")]
    status = revalue(holdings, balanced_target, as_of=as_of, refresh=False, cache={})
    assert status.total_value == 100
    assert status.stale_prices == ["missing.us"]
