from __future__ import annotations

import pytest

from asset_allocator.projection import project


def test_zero_return_is_just_contributions() -> None:
    rows = project(0.0, 100.0, 0.0, 1)
    assert len(rows) == 1
    row = rows[0]
    assert row.contributed == 1200.0
    assert row.nominal == 1200.0
    assert row.growth == 0.0
    assert row.real == 1200.0  # no inflation


def test_positive_return_grows_above_contributions() -> None:
    rows = project(1000.0, 0.0, 12.0, 1)
    row = rows[0]
    assert row.nominal > 1000.0
    assert row.growth > 0.0
    assert row.contributed == 1000.0


def test_inflation_makes_real_below_nominal() -> None:
    rows = project(1000.0, 0.0, 0.0, 2, inflation_pct=10.0)
    assert rows[-1].real < rows[-1].nominal


def test_row_count_equals_years() -> None:
    assert len(project(1000.0, 50.0, 5.0, 10)) == 10


def test_years_must_be_positive() -> None:
    with pytest.raises(ValueError):
        project(1000.0, 0.0, 5.0, 0)


def test_negative_monthly_raises() -> None:
    with pytest.raises(ValueError):
        project(1000.0, -10.0, 5.0, 1)
