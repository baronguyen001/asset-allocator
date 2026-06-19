"""Cash-flow / budget tracking: income and expense items persisted in the store.

NOT FINANCIAL ADVICE. This is arithmetic over user-supplied income and expense items
(monthly or yearly), normalized to a monthly view. It does not recommend a budget or tell
anyone what to earn, spend, or save.
"""

from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Any

from asset_allocator.models import BudgetSummary, CashflowItem

KINDS = ("income", "expense")
FREQS = ("monthly", "yearly")


class BudgetError(ValueError):
    """Raised for invalid cash-flow input."""


def _items(data: dict[str, Any]) -> list[Any]:
    items = data.setdefault("cashflow", [])
    if not isinstance(items, list):
        raise BudgetError("Portfolio store field 'cashflow' must be a list.")
    return items


def monthly_value(item: CashflowItem) -> float:
    """Normalize an item's amount to a monthly figure (yearly items divided by 12)."""
    return item.amount / 12.0 if item.freq == "yearly" else item.amount


def _validate(item: CashflowItem) -> CashflowItem:
    if item.kind not in KINDS:
        raise BudgetError(f"kind must be one of {', '.join(KINDS)}, got {item.kind!r}.")
    if item.freq not in FREQS:
        raise BudgetError(f"freq must be one of {', '.join(FREQS)}, got {item.freq!r}.")
    if not item.label:
        raise BudgetError("label is required.")
    if item.amount < 0:
        raise BudgetError("amount must be non-negative.")
    return item


def add_item(data: dict[str, Any], item: CashflowItem) -> None:
    _items(data).append(asdict(_validate(item)))


def remove_item(data: dict[str, Any], kind: str, label: str) -> bool:
    items = _items(data)
    before = len(items)
    data["cashflow"] = [
        it
        for it in items
        if not (isinstance(it, dict) and it.get("kind") == kind and it.get("label") == label)
    ]
    return len(data["cashflow"]) != before


def load_items(data: dict[str, Any], kind: str | None = None) -> list[CashflowItem]:
    out: list[CashflowItem] = []
    for raw in _items(data):
        if not isinstance(raw, dict) or "label" not in raw:
            continue
        item = CashflowItem(
            kind=str(raw.get("kind", "expense")),
            label=str(raw.get("label", "")),
            amount=float(raw.get("amount", 0.0)),
            freq=str(raw.get("freq", "monthly")),
            category=str(raw.get("category", "")),
        )
        if kind is None or item.kind == kind:
            out.append(item)
    return out


def summarize(data: dict[str, Any]) -> BudgetSummary:
    income = load_items(data, "income")
    expense = load_items(data, "expense")
    m_in = sum(monthly_value(i) for i in income)
    m_out = sum(monthly_value(e) for e in expense)
    surplus = m_in - m_out
    rate = (surplus / m_in * 100.0) if m_in else 0.0
    return BudgetSummary(
        monthly_income=round(m_in, 2),
        monthly_expense=round(m_out, 2),
        monthly_surplus=round(surplus, 2),
        savings_rate=round(rate, 2),
        annual_income=round(m_in * 12.0, 2),
        annual_expense=round(m_out * 12.0, 2),
        annual_surplus=round(surplus * 12.0, 2),
        income_items=len(income),
        expense_items=len(expense),
    )


def import_csv(data: dict[str, Any], text: str, *, replace: bool = False) -> int:
    """Bulk-load cash-flow items from CSV columns kind,label,amount[,freq,category]."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise BudgetError("CSV has no header row.")
    missing = [col for col in ("kind", "label", "amount") if col not in reader.fieldnames]
    if missing:
        raise BudgetError(f"CSV is missing required column(s): {', '.join(missing)}.")
    parsed: list[CashflowItem] = []
    for offset, row in enumerate(reader):
        line = offset + 2
        label = (row.get("label") or "").strip()
        if not label:
            continue
        try:
            amount = float((row.get("amount") or "0").strip())
        except ValueError as exc:
            raise BudgetError(f"Row {line}: amount must be a number.") from exc
        parsed.append(
            _validate(
                CashflowItem(
                    kind=(row.get("kind") or "expense").strip(),
                    label=label,
                    amount=amount,
                    freq=(row.get("freq") or "monthly").strip() or "monthly",
                    category=(row.get("category") or "").strip(),
                )
            )
        )
    if not parsed:
        raise BudgetError("CSV contained no cash-flow rows.")
    items = _items(data)
    if replace:
        items.clear()
    items.extend(asdict(item) for item in parsed)
    return len(parsed)


def render_budget(data: dict[str, Any]) -> str:
    """Render income/expense as a fixed-width text table plus the monthly surplus line."""
    summary = summarize(data)
    lines = ["Income (monthly-equivalent):"]
    for item in load_items(data, "income"):
        lines.append(f"  {item.label:<28} {monthly_value(item):>10.2f}  ({item.freq})")
    lines.append(f"  {'= total income / mo':<28} {summary.monthly_income:>10.2f}")
    lines.append("")
    lines.append("Expenses (monthly-equivalent):")
    for item in load_items(data, "expense"):
        cat = f" [{item.category}]" if item.category else ""
        lines.append(f"  {item.label:<28} {monthly_value(item):>10.2f}  ({item.freq}){cat}")
    lines.append(f"  {'= total expense / mo':<28} {summary.monthly_expense:>10.2f}")
    lines.append("")
    lines.append(
        f"Monthly surplus: {summary.monthly_surplus:.2f} "
        f"(savings rate {summary.savings_rate:.1f}%) | annual surplus {summary.annual_surplus:.2f}"
    )
    return "\n".join(lines)
