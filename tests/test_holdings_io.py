from __future__ import annotations

from typing import Any

import pytest

from asset_allocator.holdings_io import HoldingImportError, import_into, parse_holdings_csv

_CSV = (
    "bucket,label,kind,cost_basis,quantity,ticker,apy,opened,valuation_override\n"
    "equity,Demo Equity,market,3000,10,demo.us,,,\n"
    "bonds,Demo Bonds,accrual,1000,,,4,2026-01-01,\n"
    "real_estate,Demo Property,static,5000,,,,,5100\n"
    "TOTAL,,,,,,,,\n"
)


def test_parse_basic_skips_total_row() -> None:
    holdings = parse_holdings_csv(_CSV)
    assert len(holdings) == 3
    equity = holdings[0]
    assert equity.bucket == "equity"
    assert equity.kind == "market"
    assert equity.cost_basis == 3000.0
    assert equity.quantity == 10.0
    assert equity.ticker == "demo.us"
    assert holdings[1].apy == 4.0
    assert holdings[1].opened == "2026-01-01"
    assert holdings[2].valuation_override == 5100.0


def test_missing_required_column_raises() -> None:
    with pytest.raises(HoldingImportError, match="missing required column"):
        parse_holdings_csv("bucket,label,kind\nequity,Demo,market\n")


def test_unknown_bucket_raises() -> None:
    with pytest.raises(HoldingImportError, match="unknown bucket"):
        parse_holdings_csv("bucket,label,kind,cost_basis\nbogus,Demo,market,1\n")


def test_unknown_kind_raises() -> None:
    with pytest.raises(HoldingImportError, match="unknown kind"):
        parse_holdings_csv("bucket,label,kind,cost_basis\nequity,Demo,bogus,1\n")


def test_bad_number_raises() -> None:
    with pytest.raises(HoldingImportError, match="must be a number"):
        parse_holdings_csv("bucket,label,kind,cost_basis\nequity,Demo,market,abc\n")


def test_empty_rows_raises() -> None:
    with pytest.raises(HoldingImportError, match="no holding rows"):
        parse_holdings_csv("bucket,label,kind,cost_basis\nTOTAL,,,\n")


def test_import_into_merge_then_replace() -> None:
    data: dict[str, Any] = {"holdings": [{"bucket": "cash", "label": "Old", "kind": "static"}]}
    holdings = parse_holdings_csv(_CSV)
    added = import_into(data, holdings, replace=False)
    assert added == 3
    assert len(data["holdings"]) == 4  # 1 existing + 3 merged
    import_into(data, holdings, replace=True)
    assert len(data["holdings"]) == 3  # existing cleared


def test_sample_holdings_file_parses() -> None:
    with open("examples/sample_holdings.csv", encoding="utf-8") as handle:
        holdings = parse_holdings_csv(handle.read())
    assert len(holdings) == 7
