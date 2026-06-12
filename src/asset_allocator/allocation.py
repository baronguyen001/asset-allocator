"""Illustrative target allocation and rebalance math.

NOT FINANCIAL ADVICE. Model weights are user-tunable defaults for arithmetic and
education. They are not financial advice, recommendations, or instructions to trade.
"""

from __future__ import annotations

from asset_allocator.config import ASSET_CLASSES, MODEL_TEMPLATES, REBALANCE_BAND
from asset_allocator.models import PortfolioStatus, RebalanceAction, RiskProfile, TargetAllocation


def _normalise(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Target weights must sum to a positive number.")
    normalised = {bucket: weights.get(bucket, 0.0) * 100.0 / total for bucket in ASSET_CLASSES}
    diff = 100.0 - sum(normalised.values())
    normalised[ASSET_CLASSES[0]] += diff
    return {bucket: round(value, 6) for bucket, value in normalised.items()}


def target_allocation(profile: RiskProfile, *, glide_path: bool = False) -> TargetAllocation:
    if profile.name == "custom":
        raise ValueError(
            "Custom profiles require explicit weights; no default custom weights exist."
        )
    if profile.name not in MODEL_TEMPLATES:
        raise ValueError(f"Unknown profile {profile.name!r}.")
    weights = dict(MODEL_TEMPLATES[profile.name])
    if glide_path and profile.age is not None:
        current_equity = weights["equity"]
        desired_equity = max(current_equity * 0.5, min(90.0, 110.0 - profile.age))
        delta = desired_equity - current_equity
        other_total = 100.0 - current_equity
        weights["equity"] = desired_equity
        if other_total > 0:
            for bucket in ASSET_CLASSES:
                if bucket != "equity":
                    weights[bucket] -= delta * (weights[bucket] / other_total)
    return TargetAllocation(profile_name=profile.name, weights=_normalise(weights))


def split_amount(target: TargetAllocation, total: float) -> dict[str, float]:
    return {bucket: round(total * weight / 100.0, 2) for bucket, weight in target.weights.items()}


def rebalance(status: PortfolioStatus, *, band: float = REBALANCE_BAND) -> list[RebalanceAction]:
    actions: list[RebalanceAction] = []
    for bucket in status.buckets:
        target_value = status.total_value * bucket.target_weight / 100.0
        amount = abs(target_value - bucket.market_value)
        if bucket.drift > band:
            direction = "sell"
        elif bucket.drift < -band:
            direction = "buy"
        else:
            direction = "hold"
            amount = 0.0
        actions.append(
            RebalanceAction(
                bucket=bucket.bucket,
                direction=direction,
                amount=round(amount, 2),
                drift=round(bucket.drift, 4),
            )
        )
    return actions
