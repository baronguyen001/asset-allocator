from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskProfile:
    name: str
    score: int
    horizon_years: int
    age: int | None
    notes: str = ""


@dataclass
class TargetAllocation:
    profile_name: str
    weights: dict[str, float]


@dataclass
class Holding:
    bucket: str
    label: str
    kind: str
    cost_basis: float
    quantity: float = 0.0
    ticker: str | None = None
    apy: float = 0.0
    opened: str | None = None
    valuation_override: float | None = None


@dataclass
class BucketStatus:
    bucket: str
    market_value: float
    cost_basis: float
    pnl: float
    pnl_pct: float
    current_weight: float
    target_weight: float
    drift: float


@dataclass
class PortfolioStatus:
    as_of: str
    base_ccy: str
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    buckets: list[BucketStatus]
    stale_prices: list[str]


@dataclass
class RebalanceAction:
    bucket: str
    direction: str
    amount: float
    drift: float


@dataclass
class ContributionItem:
    bucket: str
    amount: float
    current_weight: float
    projected_weight: float
    target_weight: float


@dataclass
class Snapshot:
    as_of: str
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    weights: dict[str, float]
    note: str = ""


@dataclass
class PeriodReturn:
    start: str
    end: str
    start_value: float
    end_value: float
    change: float
    change_pct: float
    last_change: float
    last_change_pct: float
    snapshots: int
