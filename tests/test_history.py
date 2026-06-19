from __future__ import annotations

from typing import Any

import pytest

from asset_allocator.history import load_history, period_return, record_snapshot, render_history
from asset_allocator.models import BucketStatus, PortfolioStatus


def _status(value: float, as_of: str) -> PortfolioStatus:
    return PortfolioStatus(
        as_of=as_of,
        base_ccy="USD",
        total_value=value,
        total_cost=1000.0,
        total_pnl=value - 1000.0,
        total_pnl_pct=round((value - 1000.0) / 1000.0 * 100.0, 4),
        stale_prices=[],
        buckets=[BucketStatus("equity", value, 1000.0, value - 1000.0, 0.0, 100.0, 100.0, 0.0)],
    )


def test_record_and_load_snapshots() -> None:
    data: dict[str, Any] = {}
    record_snapshot(data, _status(1000.0, "2026-06-01T00:00:00+00:00"), note="start")
    record_snapshot(data, _status(1100.0, "2026-06-02T00:00:00+00:00"))
    snaps = load_history(data)
    assert len(snaps) == 2
    assert snaps[0].note == "start"
    assert snaps[1].total_value == 1100.0
    assert snaps[0].weights["equity"] == 100.0


def test_period_return_none_with_fewer_than_two() -> None:
    data: dict[str, Any] = {}
    assert period_return(data) is None
    record_snapshot(data, _status(1000.0, "2026-06-01T00:00:00+00:00"))
    assert period_return(data) is None


def test_period_return_computes_change() -> None:
    data: dict[str, Any] = {}
    record_snapshot(data, _status(1000.0, "2026-06-01T00:00:00+00:00"))
    record_snapshot(data, _status(1050.0, "2026-06-02T00:00:00+00:00"))
    record_snapshot(data, _status(1200.0, "2026-06-03T00:00:00+00:00"))
    summary = period_return(data)
    assert summary is not None
    assert summary.change == 200.0
    assert summary.change_pct == 20.0
    assert summary.last_change == 150.0
    assert summary.snapshots == 3


def test_render_history_empty_then_populated() -> None:
    data: dict[str, Any] = {}
    assert "No snapshots" in render_history(data)
    record_snapshot(data, _status(1000.0, "2026-06-01T00:00:00+00:00"))
    record_snapshot(data, _status(1100.0, "2026-06-02T00:00:00+00:00"))
    text = render_history(data)
    assert "Value" in text
    assert "Period" in text


def test_load_history_skips_malformed_entries() -> None:
    data: dict[str, Any] = {
        "history": [
            {"as_of": "2026-06-01T00:00:00+00:00", "total_value": 1.0},
            "garbage",
            {"no_as_of": 1},
        ]
    }
    assert len(load_history(data)) == 1


def test_history_must_be_a_list() -> None:
    data: dict[str, Any] = {"history": "not a list"}
    with pytest.raises(ValueError):
        load_history(data)
