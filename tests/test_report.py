from __future__ import annotations

from asset_allocator.models import BucketStatus, BudgetSummary, PortfolioStatus, Snapshot
from asset_allocator.report import render_status, render_status_csv, write_dashboard_html


def sample_status() -> PortfolioStatus:
    return PortfolioStatus(
        as_of="2026-06-12T00:00:00+00:00",
        base_ccy="USD",
        total_value=100,
        total_cost=90,
        total_pnl=10,
        total_pnl_pct=11.1111,
        stale_prices=["demo.us"],
        buckets=[BucketStatus("equity", 100, 90, 10, 11.1111, 100, 40, 60)],
    )


def test_render_status_formats() -> None:
    status = sample_status()
    assert "Portfolio status" in str(render_status(status, "text"))
    assert "| Bucket |" in str(render_status(status, "md"))
    assert render_status(status, "dict")["total_value"] == 100  # type: ignore[index]


def test_write_dashboard_html_self_contained(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "dashboard.html"
    write_dashboard_html(sample_status(), str(path))
    html = path.read_text(encoding="utf-8")
    assert "<svg" in html
    assert "https://" not in html
    assert "NOT FINANCIAL ADVICE" in html


def test_render_status_csv_has_header_and_total() -> None:
    csv_text = render_status_csv(sample_status())
    assert csv_text.startswith("bucket,market_value")
    assert "equity," in csv_text
    assert "TOTAL," in csv_text


def test_dashboard_embeds_history_sparkline(tmp_path) -> None:  # type: ignore[no-untyped-def]
    history = [
        Snapshot("2026-06-01T00:00:00+00:00", 100.0, 90.0, 10.0, 11.0, {"equity": 100.0}),
        Snapshot("2026-06-02T00:00:00+00:00", 120.0, 90.0, 30.0, 33.0, {"equity": 100.0}),
    ]
    path = tmp_path / "dashboard.html"
    write_dashboard_html(sample_status(), str(path), history=history)
    html = path.read_text(encoding="utf-8")
    assert "Value history" in html
    assert "<polyline" in html
    assert "https://" not in html


def test_dashboard_has_kpi_cards_english(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "en.html"
    write_dashboard_html(sample_status(), str(path), lang="en")
    html = path.read_text(encoding="utf-8")
    assert "Net worth" in html
    assert "Largest bucket" in html
    assert 'class="card"' in html


def test_dashboard_vietnamese(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "vi.html"
    write_dashboard_html(sample_status(), str(path), lang="vi")
    html = path.read_text(encoding="utf-8")
    assert 'lang="vi"' in html
    assert "Giá trị ròng" in html  # net worth
    assert "Cổ phiếu" in html  # localized equity bucket
    assert "KHÔNG PHẢI LỜI KHUYÊN" in html  # vi disclaimer
    assert "https://" not in html


def test_dashboard_cashflow_panel(tmp_path) -> None:  # type: ignore[no-untyped-def]
    budget = BudgetSummary(
        monthly_income=90.0,
        monthly_expense=35.0,
        monthly_surplus=55.0,
        savings_rate=61.1,
        annual_income=1080.0,
        annual_expense=420.0,
        annual_surplus=660.0,
        income_items=2,
        expense_items=10,
    )
    path = tmp_path / "cf.html"
    write_dashboard_html(sample_status(), str(path), lang="vi", budget=budget)
    html = path.read_text(encoding="utf-8")
    assert "Dòng tiền" in html
    assert "Thặng dư / tháng" in html
    assert "cf-row" in html


def test_dashboard_no_cashflow_panel_when_empty(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "no_cf.html"
    write_dashboard_html(sample_status(), str(path), lang="en")
    # The .cf-row CSS rule always exists; assert the rendered cash-flow panel element does not.
    assert '<div class="cf-row">' not in path.read_text(encoding="utf-8")
