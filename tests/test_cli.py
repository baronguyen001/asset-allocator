from __future__ import annotations

import json
import shutil

from asset_allocator.cli import main


def test_help(capsys) -> None:  # type: ignore[no-untyped-def]
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "Keyless asset allocation CLI" in capsys.readouterr().out


def test_init_from_file_and_plan_json(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    store = tmp_path / "portfolio.json"
    assert main(["init", "--from-file", "examples/sample_answers.json", "--store", str(store)]) == 0
    assert "NOT FINANCIAL ADVICE" in capsys.readouterr().out
    assert main(["plan", "--amount", "100000", "--json", "--store", str(store)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert sum(payload["amounts"].values()) == 100000


def test_status_rebalance_report_offline(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    store = tmp_path / "sample_portfolio.json"
    shutil.copyfile("examples/sample_portfolio.json", store)
    assert main(["status", "--no-refresh", "--store", str(store)]) == 0
    assert "Portfolio status" in capsys.readouterr().out
    assert main(["rebalance", "--json", "--store", str(store)]) == 0
    assert json.loads(capsys.readouterr().out)
    html = tmp_path / "dashboard.html"
    assert main(["report", "--html", str(html), "--no-refresh", "--store", str(store)]) == 0
    assert html.exists()
