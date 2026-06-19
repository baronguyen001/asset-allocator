"""Long-horizon net-worth goals (milestone years) tracked in the store.

NOT FINANCIAL ADVICE. Progress is net-worth / target arithmetic; "required return" is the
constant annual growth that would close the gap by the target year — a yardstick, not a
forecast, and it ignores future contributions and any business/cash-flow income.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from asset_allocator.models import GoalItem, GoalProgress


class GoalError(ValueError):
    """Raised for invalid goal input."""


def _items(data: dict[str, Any]) -> list[Any]:
    goals = data.setdefault("goals", [])
    if not isinstance(goals, list):
        raise GoalError("Portfolio store field 'goals' must be a list.")
    return goals


def _validate(goal: GoalItem) -> GoalItem:
    if not goal.label:
        raise GoalError("Goal label is required.")
    if goal.year < 1900:
        raise GoalError(f"Goal year looks invalid: {goal.year}.")
    if goal.target <= 0:
        raise GoalError("Goal target must be positive.")
    return goal


def add_goal(data: dict[str, Any], goal: GoalItem) -> None:
    _items(data).append(asdict(_validate(goal)))


def remove_goal(data: dict[str, Any], year: int) -> bool:
    items = _items(data)
    before = len(items)
    data["goals"] = [
        g for g in items if not (isinstance(g, dict) and int(g.get("year", 0)) == year)
    ]
    return len(data["goals"]) != before


def load_goals(data: dict[str, Any]) -> list[GoalItem]:
    out: list[GoalItem] = []
    for raw in _items(data):
        if not isinstance(raw, dict) or "year" not in raw:
            continue
        out.append(
            GoalItem(
                year=int(raw.get("year", 0)),
                label=str(raw.get("label", "")),
                target=float(raw.get("target", 0.0)),
            )
        )
    return sorted(out, key=lambda goal: goal.year)


def goal_progress(goal: GoalItem, net_worth: float, as_of_year: int) -> GoalProgress:
    pct = (net_worth / goal.target * 100.0) if goal.target else 0.0
    years_left = max(0, goal.year - as_of_year)
    if years_left > 0 and net_worth > 0 and goal.target > 0:
        required_cagr = ((goal.target / net_worth) ** (1.0 / years_left) - 1.0) * 100.0
    else:
        required_cagr = 0.0
    return GoalProgress(
        year=goal.year,
        label=goal.label,
        target=goal.target,
        net_worth=round(net_worth, 2),
        progress_pct=round(pct, 2),
        gap=round(goal.target - net_worth, 2),
        years_left=years_left,
        required_cagr=round(required_cagr, 2),
    )
