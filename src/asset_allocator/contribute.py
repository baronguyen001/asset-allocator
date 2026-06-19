"""Buy-only cash-flow rebalancing (DCA contribution planner).

NOT FINANCIAL ADVICE. This module computes how a fresh cash contribution could be split
across buckets to move CURRENT weights toward the illustrative target weights using
deposits only (no selling). It is arithmetic on user-supplied inputs and illustrative,
user-tunable defaults; it is not advice, a recommendation, or an instruction to trade.
"""

from __future__ import annotations

from asset_allocator.config import ASSET_CLASSES
from asset_allocator.models import ContributionItem, PortfolioStatus


def _round_to_total(allocation: dict[str, float], amount: float) -> dict[str, float]:
    """Round each allocation to cents and push the rounding remainder onto the largest."""
    rounded = {bucket: round(value, 2) for bucket, value in allocation.items()}
    diff = round(amount - sum(rounded.values()), 2)
    if diff != 0.0 and rounded:
        target_bucket = max(rounded, key=lambda bucket: rounded[bucket])
        rounded[target_bucket] = round(rounded[target_bucket] + diff, 2)
    return rounded


def plan_contribution(status: PortfolioStatus, amount: float) -> list[ContributionItem]:
    """Split a fresh contribution across buckets, buy-only, toward the target weights.

    The plan first water-fills the buckets that are below their post-contribution target
    value (proportional to how far each is behind). If the contribution is larger than the
    total shortfall, the remainder is spread by target weight. No bucket is ever sold.
    """
    if amount < 0:
        raise ValueError("Contribution amount must be non-negative.")
    current = {bucket.bucket: bucket.market_value for bucket in status.buckets}
    targets = {bucket.bucket: bucket.target_weight for bucket in status.buckets}
    new_total = status.total_value + amount
    target_total = sum(targets.values()) or 1.0

    deficits = {
        bucket: max(
            0.0,
            new_total * targets.get(bucket, 0.0) / 100.0 - current.get(bucket, 0.0),
        )
        for bucket in ASSET_CLASSES
    }
    total_deficit = sum(deficits.values())

    allocation = {bucket: 0.0 for bucket in ASSET_CLASSES}
    if amount > 0:
        if total_deficit <= 0:
            for bucket in ASSET_CLASSES:
                allocation[bucket] = amount * targets.get(bucket, 0.0) / target_total
        elif amount <= total_deficit:
            for bucket in ASSET_CLASSES:
                allocation[bucket] = amount * deficits[bucket] / total_deficit
        else:
            remainder = amount - total_deficit
            for bucket in ASSET_CLASSES:
                allocation[bucket] = (
                    deficits[bucket] + remainder * targets.get(bucket, 0.0) / target_total
                )

    allocation = _round_to_total(allocation, amount)

    items: list[ContributionItem] = []
    for bucket in ASSET_CLASSES:
        prior = current.get(bucket, 0.0)
        new_value = prior + allocation[bucket]
        current_weight = (prior / status.total_value * 100.0) if status.total_value else 0.0
        projected_weight = (new_value / new_total * 100.0) if new_total else 0.0
        items.append(
            ContributionItem(
                bucket=bucket,
                amount=allocation[bucket],
                current_weight=round(current_weight, 4),
                projected_weight=round(projected_weight, 4),
                target_weight=round(targets.get(bucket, 0.0), 4),
            )
        )
    return items
