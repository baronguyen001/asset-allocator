from __future__ import annotations

from typing import Any

import pytest

from asset_allocator.goals import GoalError, add_goal, goal_progress, load_goals, remove_goal
from asset_allocator.models import GoalItem


def test_add_and_load_sorted_by_year() -> None:
    data: dict[str, Any] = {}
    add_goal(data, GoalItem(2042, "Empire", 1055000))
    add_goal(data, GoalItem(2032, "Freedom", 155000))
    years = [g.year for g in load_goals(data)]
    assert years == [2032, 2042]


def test_progress_and_required_cagr() -> None:
    progress = goal_progress(GoalItem(2032, "Freedom", 155000), 34196.0, 2026)
    assert progress.years_left == 6
    assert 21.0 < progress.progress_pct < 23.0
    assert progress.gap == round(155000 - 34196.0, 2)
    assert 25.0 < progress.required_cagr < 33.0  # ~28.8%/yr


def test_progress_with_no_years_left() -> None:
    progress = goal_progress(GoalItem(2026, "Now", 100), 50.0, 2026)
    assert progress.years_left == 0
    assert progress.required_cagr == 0.0


def test_remove_goal() -> None:
    data: dict[str, Any] = {}
    add_goal(data, GoalItem(2032, "X", 100))
    assert remove_goal(data, 2032) is True
    assert remove_goal(data, 2032) is False


def test_validation() -> None:
    data: dict[str, Any] = {}
    with pytest.raises(GoalError):
        add_goal(data, GoalItem(2032, "", 100))
    with pytest.raises(GoalError):
        add_goal(data, GoalItem(1800, "X", 100))
    with pytest.raises(GoalError):
        add_goal(data, GoalItem(2032, "X", 0))


def test_goals_field_must_be_list() -> None:
    with pytest.raises(GoalError):
        load_goals({"goals": "not a list"})
