"""Tests for tax-lot cost-basis tracking (v0.7)."""

from __future__ import annotations

import pytest

from asset_allocator.cli import main
from asset_allocator.taxlot import (
    OversellError,
    Transaction,
    compute_taxlots,
)

# Buys: 10 @ 100, 10 @ 120; then sell 15 @ 130.
TXS = [
    Transaction("buy", 10, 100, "2024-01-01"),
    Transaction("buy", 10, 120, "2024-02-01"),
    Transaction("sell", 15, 130, "2024-03-01"),
]


def test_fifo_realized_gain_and_remaining() -> None:
    r = compute_taxlots(TXS, "fifo")
    # cost = 10*100 + 5*120 = 1600; proceeds = 15*130 = 1950; gain = 350
    assert r.total_cost_sold == pytest.approx(1600)
    assert r.total_proceeds == pytest.approx(1950)
    assert r.realized_gain == pytest.approx(350)
    # remaining 5 units from the 120 lot
    assert r.remaining_quantity == pytest.approx(5)
    assert r.remaining_cost_basis == pytest.approx(600)
    assert r.remaining_avg_cost == pytest.approx(120)


def test_average_realized_gain_and_remaining() -> None:
    r = compute_taxlots(TXS, "average")
    # avg = (1000 + 1200) / 20 = 110; cost = 15*110 = 1650; gain = 300
    assert r.total_cost_sold == pytest.approx(1650)
    assert r.realized_gain == pytest.approx(300)
    assert r.remaining_quantity == pytest.approx(5)
    assert r.remaining_cost_basis == pytest.approx(550)
    assert r.remaining_avg_cost == pytest.approx(110)


def test_methods_disagree_but_remaining_qty_matches() -> None:
    fifo = compute_taxlots(TXS, "fifo")
    avg = compute_taxlots(TXS, "average")
    assert fifo.realized_gain != avg.realized_gain
    assert fifo.remaining_quantity == avg.remaining_quantity


def test_oversell_raises() -> None:
    txs = [Transaction("buy", 10, 100), Transaction("sell", 11, 130)]
    with pytest.raises(OversellError):
        compute_taxlots(txs, "fifo")
    with pytest.raises(OversellError):
        compute_taxlots(txs, "average")


def test_validation() -> None:
    with pytest.raises(ValueError):
        compute_taxlots([Transaction("hold", 1, 1)], "fifo")
    with pytest.raises(ValueError):
        compute_taxlots([Transaction("buy", -1, 1)], "fifo")
    with pytest.raises(ValueError):
        compute_taxlots([], "lifo")


def test_no_sales_keeps_full_basis() -> None:
    r = compute_taxlots([Transaction("buy", 5, 200)], "fifo")
    assert r.realized_gain == 0
    assert r.remaining_quantity == pytest.approx(5)
    assert r.remaining_cost_basis == pytest.approx(1000)


def _write_csv(tmp_path) -> str:
    path = tmp_path / "tx.csv"
    path.write_text(
        "action,quantity,price,date\nbuy,10,100,2024-01-01\nbuy,10,120,2024-02-01\nsell,15,130,2024-03-01\n",
        encoding="utf-8",
    )
    return str(path)


def test_cli_taxlot_text(tmp_path, capsys) -> None:
    rc = main(["taxlot", "--csv", _write_csv(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Method: fifo" in out
    assert "Realized gain/loss" in out


def test_cli_taxlot_json_average(tmp_path, capsys) -> None:
    import json

    rc = main(["taxlot", "--csv", _write_csv(tmp_path), "--method", "average", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["method"] == "average"
    assert data["realized_gain"] == pytest.approx(300)


def test_cli_taxlot_oversell_errors(tmp_path, capsys) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("action,quantity,price\nbuy,1,100\nsell,5,100\n", encoding="utf-8")
    rc = main(["taxlot", "--csv", str(path)])
    assert rc == 2
    assert "taxlot error" in capsys.readouterr().err
