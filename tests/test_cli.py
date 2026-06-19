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


def test_contribute_snapshot_history_export(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    store = tmp_path / "sample_portfolio.json"
    shutil.copyfile("examples/sample_portfolio.json", store)

    assert (
        main(["contribute", "--amount", "5000", "--json", "--no-refresh", "--store", str(store)])
        == 0
    )
    items = json.loads(capsys.readouterr().out)
    assert round(sum(item["amount"] for item in items), 2) == 5000.0

    assert main(["snapshot", "--no-refresh", "--note", "first", "--store", str(store)]) == 0
    capsys.readouterr()
    assert main(["snapshot", "--no-refresh", "--store", str(store)]) == 0
    capsys.readouterr()

    assert main(["history", "--json", "--store", str(store)]) == 0
    history = json.loads(capsys.readouterr().out)
    assert len(history["history"]) == 2

    out = tmp_path / "status.csv"
    export_args = [
        "export",
        "--format",
        "csv",
        "--out",
        str(out),
        "--no-refresh",
        "--store",
        str(store),
    ]
    assert main(export_args) == 0
    assert "bucket,market_value" in out.read_text(encoding="utf-8")


def test_import_set_target_project(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    store = tmp_path / "portfolio.json"

    assert (
        main(
            ["import", "--csv", "examples/sample_holdings.csv", "--replace", "--store", str(store)]
        )
        == 0
    )
    capsys.readouterr()
    data = json.loads(store.read_text(encoding="utf-8"))
    assert len(data["holdings"]) == 7

    assert (
        main(["set-target", "--weight", "equity=60", "--weight", "bonds=40", "--store", str(store)])
        == 0
    )
    assert "custom" in capsys.readouterr().out
    data = json.loads(store.read_text(encoding="utf-8"))
    assert data["target"]["profile_name"] == "custom"
    assert len(data["holdings"]) == 7  # set-target preserves holdings

    project_args = [
        "project",
        "--years",
        "3",
        "--monthly",
        "100",
        "--annual-return",
        "5",
        "--initial",
        "1000",
        "--json",
        "--store",
        str(store),
    ]
    assert main(project_args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 3
    assert rows[-1]["nominal"] > rows[-1]["contributed"]
