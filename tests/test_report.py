from __future__ import annotations

from asset_allocator.models import BucketStatus, PortfolioStatus
from asset_allocator.report import render_status, write_dashboard_html


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
