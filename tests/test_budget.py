from __future__ import annotations

from typing import Any

import pytest

from asset_allocator.budget import (
    BudgetError,
    add_item,
    import_csv,
    load_items,
    monthly_value,
    remove_item,
    summarize,
)
from asset_allocator.models import CashflowItem


def test_monthly_value_normalizes_yearly() -> None:
    assert monthly_value(CashflowItem("expense", "Tet", 120, "yearly")) == 10.0
    assert monthly_value(CashflowItem("income", "Salary", 80, "monthly")) == 80.0


def test_add_and_summarize() -> None:
    data: dict[str, Any] = {}
    add_item(data, CashflowItem("income", "Salary", 80))
    add_item(data, CashflowItem("income", "Rent room", 10))
    add_item(data, CashflowItem("expense", "Food", 8))
    add_item(data, CashflowItem("expense", "Insurance", 60, "yearly"))
    summary = summarize(data)
    assert summary.monthly_income == 90.0
    assert summary.monthly_expense == 13.0  # 8 + 60/12
    assert summary.monthly_surplus == 77.0
    assert summary.annual_surplus == 924.0
    assert summary.income_items == 2
    assert summary.expense_items == 2


def test_remove_item() -> None:
    data: dict[str, Any] = {}
    add_item(data, CashflowItem("expense", "Food", 8))
    assert remove_item(data, "expense", "Food") is True
    assert remove_item(data, "expense", "Food") is False


def test_validation_rejects_bad_input() -> None:
    data: dict[str, Any] = {}
    with pytest.raises(BudgetError):
        add_item(data, CashflowItem("bogus", "X", 1))
    with pytest.raises(BudgetError):
        add_item(data, CashflowItem("income", "X", 1, "weekly"))
    with pytest.raises(BudgetError):
        add_item(data, CashflowItem("income", "", 1))
    with pytest.raises(BudgetError):
        add_item(data, CashflowItem("income", "X", -5))


def test_import_csv_and_load() -> None:
    data: dict[str, Any] = {}
    text = (
        "kind,label,amount,freq,category\n"
        "income,Salary,80,monthly,\n"
        "expense,Tet,30,yearly,holiday\n"
    )
    assert import_csv(data, text) == 2
    assert len(load_items(data)) == 2
    summary = summarize(data)
    assert summary.monthly_income == 80.0
    assert summary.monthly_expense == 2.5  # 30 / 12


def test_import_csv_missing_column() -> None:
    data: dict[str, Any] = {}
    with pytest.raises(BudgetError):
        import_csv(data, "label,amount\nX,1\n")


def test_cashflow_field_must_be_list() -> None:
    with pytest.raises(BudgetError):
        load_items({"cashflow": "not a list"})
