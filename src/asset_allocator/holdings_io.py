"""Load holdings from a CSV file (the inverse of `allocate export`).

NOT FINANCIAL ADVICE. This only parses user-supplied rows into holding records; it does
not fetch prices, value anything, or recommend any position.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from asset_allocator.config import ASSET_CLASSES
from asset_allocator.models import Holding

_KINDS = {"market", "accrual", "static"}
_REQUIRED = ("bucket", "label", "kind", "cost_basis")


class HoldingImportError(ValueError):
    """Raised when a holdings CSV cannot be parsed into valid holdings."""


def _num(row: dict[str, str], key: str, line: int, *, default: float = 0.0) -> float:
    raw = (row.get(key) or "").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise HoldingImportError(f"Row {line}: {key!r} must be a number, got {raw!r}.") from exc


def _opt_num(row: dict[str, str], key: str, line: int) -> float | None:
    raw = (row.get(key) or "").strip()
    if raw == "":
        return None
    return _num(row, key, line)


def parse_holdings_csv(text: str) -> list[Holding]:
    """Parse CSV text into a list of validated Holding records.

    Columns: bucket, label, kind, cost_basis (required) and quantity, ticker, apy,
    opened, valuation_override (optional). A leading "TOTAL" summary row is ignored
    defensively so a hand-edited sheet with a totals line still imports cleanly.
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HoldingImportError("CSV has no header row.")
    missing = [col for col in _REQUIRED if col not in reader.fieldnames]
    if missing:
        raise HoldingImportError(f"CSV is missing required column(s): {', '.join(missing)}.")
    holdings: list[Holding] = []
    for offset, row in enumerate(reader):
        line = offset + 2  # header is line 1
        bucket = (row.get("bucket") or "").strip()
        if not bucket or bucket.upper() == "TOTAL":
            continue
        if bucket not in ASSET_CLASSES:
            allowed = ", ".join(ASSET_CLASSES)
            raise HoldingImportError(
                f"Row {line}: unknown bucket {bucket!r}; expected one of {allowed}."
            )
        label = (row.get("label") or "").strip()
        if not label:
            raise HoldingImportError(f"Row {line}: 'label' is required.")
        kind = (row.get("kind") or "").strip()
        if kind not in _KINDS:
            raise HoldingImportError(
                f"Row {line}: unknown kind {kind!r}; expected one of {', '.join(sorted(_KINDS))}."
            )
        ticker_raw = (row.get("ticker") or "").strip()
        opened_raw = (row.get("opened") or "").strip()
        holdings.append(
            Holding(
                bucket=bucket,
                label=label,
                kind=kind,
                cost_basis=_num(row, "cost_basis", line),
                quantity=_num(row, "quantity", line),
                ticker=ticker_raw or None,
                apy=_num(row, "apy", line),
                opened=opened_raw or None,
                valuation_override=_opt_num(row, "valuation_override", line),
            )
        )
    if not holdings:
        raise HoldingImportError("CSV contained no holding rows.")
    return holdings


def import_into(data: dict[str, Any], holdings: list[Holding], *, replace: bool = False) -> int:
    """Merge (or replace) parsed holdings into a store dict; return the count added."""
    from dataclasses import asdict

    existing = data.setdefault("holdings", [])
    if not isinstance(existing, list):
        raise HoldingImportError("Portfolio store field 'holdings' must be a list.")
    if replace:
        existing.clear()
    existing.extend(asdict(holding) for holding in holdings)
    return len(holdings)
