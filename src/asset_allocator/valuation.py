from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from asset_allocator.config import ASSET_CLASSES, PRICE_TTL
from asset_allocator.models import BucketStatus, Holding, PortfolioStatus, TargetAllocation
from asset_allocator.prices import resolve_price
from asset_allocator.prices.base import PriceError


def _date_part(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def holding_value(h: Holding, *, as_of: str, price: float | None) -> float:
    if h.valuation_override is not None:
        return float(h.valuation_override)
    if h.kind == "market":
        if price is None:
            raise ValueError(f"Market holding {h.label!r} requires a price.")
        return price * h.quantity
    if h.kind == "accrual":
        opened = _date_part(h.opened) if h.opened else _date_part(as_of)
        days = max(0, (_date_part(as_of) - opened).days)
        return float(h.cost_basis * (1 + h.apy / 100.0) ** (days / 365.0))
    if h.kind == "static":
        return h.cost_basis
    raise ValueError(f"Unknown holding kind {h.kind!r}.")


def _coerce_holding(value: Holding | dict[str, Any]) -> Holding:
    if isinstance(value, Holding):
        return value
    return Holding(**value)


def revalue(
    holdings: Iterable[Holding | dict[str, Any]],
    target: TargetAllocation | None,
    *,
    as_of: str,
    base_ccy: str = "USD",
    refresh: bool = True,
    session: Any = None,
    cache: dict[str, Any] | None = None,
) -> PortfolioStatus:
    cache = cache if cache is not None else {}
    bucket_values = {bucket: 0.0 for bucket in ASSET_CLASSES}
    bucket_costs = {bucket: 0.0 for bucket in ASSET_CLASSES}
    stale_prices: list[str] = []
    for raw_holding in holdings:
        holding = _coerce_holding(raw_holding)
        price: float | None = None
        if holding.kind == "market" and holding.valuation_override is None:
            try:
                if refresh:
                    price, stale = resolve_price(
                        holding,
                        session=session,
                        cache=cache,
                        ttl=PRICE_TTL,
                    )
                else:
                    price, stale = resolve_price(holding, session=session, cache=cache, ttl=0)
                if stale and holding.ticker:
                    stale_prices.append(holding.ticker)
            except PriceError:
                if holding.ticker:
                    stale_prices.append(holding.ticker)
                price = None
        try:
            value = holding_value(holding, as_of=as_of, price=price)
        except ValueError:
            value = holding.cost_basis
        bucket_values[holding.bucket] = bucket_values.get(holding.bucket, 0.0) + value
        bucket_costs[holding.bucket] = bucket_costs.get(holding.bucket, 0.0) + holding.cost_basis
    total_value = sum(bucket_values.values())
    total_cost = sum(bucket_costs.values())
    buckets: list[BucketStatus] = []
    for bucket in ASSET_CLASSES:
        market_value = bucket_values[bucket]
        cost_basis = bucket_costs[bucket]
        pnl = market_value - cost_basis
        current_weight = (market_value / total_value * 100.0) if total_value else 0.0
        target_weight = target.weights.get(bucket, 0.0) if target else 0.0
        buckets.append(
            BucketStatus(
                bucket=bucket,
                market_value=round(market_value, 2),
                cost_basis=round(cost_basis, 2),
                pnl=round(pnl, 2),
                pnl_pct=round((pnl / cost_basis * 100.0) if cost_basis else 0.0, 4),
                current_weight=round(current_weight, 4),
                target_weight=round(target_weight, 4),
                drift=round(current_weight - target_weight, 4),
            )
        )
    total_pnl = total_value - total_cost
    status = PortfolioStatus(
        as_of=as_of,
        base_ccy=base_ccy,
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round((total_pnl / total_cost * 100.0) if total_cost else 0.0, 4),
        buckets=buckets,
        stale_prices=sorted(set(stale_prices)),
    )
    return status
