# ruff: noqa: E501
from __future__ import annotations

import csv
import io
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from asset_allocator.models import PortfolioStatus, Snapshot


def render_status(status: PortfolioStatus, fmt: str = "text") -> str | dict[str, Any]:
    if fmt == "dict":
        return asdict(status)
    rows = [
        (
            bucket.bucket,
            bucket.market_value,
            bucket.pnl,
            bucket.pnl_pct,
            bucket.current_weight,
            bucket.target_weight,
            bucket.drift,
        )
        for bucket in status.buckets
    ]
    if fmt == "md":
        lines = [
            f"# Portfolio status as of {status.as_of}",
            "",
            f"Total value: {status.total_value:.2f} {status.base_ccy}",
            f"Total P&L: {status.total_pnl:.2f} ({status.total_pnl_pct:.2f}%)",
            "",
            "| Bucket | Value | P&L | P&L % | Current % | Target % | Drift |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        lines.extend(
            f"| {name} | {value:.2f} | {pnl:.2f} | {pnl_pct:.2f}% | "
            f"{current:.2f}% | {target:.2f}% | {drift:.2f}% |"
            for name, value, pnl, pnl_pct, current, target, drift in rows
        )
        if status.stale_prices:
            lines.append("")
            lines.append(f"Stale prices: {', '.join(status.stale_prices)}")
        return "\n".join(lines)
    if fmt != "text":
        raise ValueError("fmt must be one of: text, md, dict")
    lines = [
        f"Portfolio status as of {status.as_of}",
        f"Total value: {status.total_value:.2f} {status.base_ccy}",
        f"Total P&L: {status.total_pnl:.2f} ({status.total_pnl_pct:.2f}%)",
        "",
        "Bucket          Value       P&L    P&L%  Current  Target   Drift",
    ]
    for name, value, pnl, pnl_pct, current, target, drift in rows:
        lines.append(
            f"{name:<12} {value:>10.2f} {pnl:>9.2f} {pnl_pct:>7.2f} "
            f"{current:>8.2f} {target:>7.2f} {drift:>7.2f}"
        )
    if status.stale_prices:
        lines.append(f"\nStale prices: {', '.join(status.stale_prices)}")
    return "\n".join(lines)


def render_status_csv(status: PortfolioStatus) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "bucket",
            "market_value",
            "cost_basis",
            "pnl",
            "pnl_pct",
            "current_weight",
            "target_weight",
            "drift",
        ]
    )
    for bucket in status.buckets:
        writer.writerow(
            [
                bucket.bucket,
                f"{bucket.market_value:.2f}",
                f"{bucket.cost_basis:.2f}",
                f"{bucket.pnl:.2f}",
                f"{bucket.pnl_pct:.4f}",
                f"{bucket.current_weight:.4f}",
                f"{bucket.target_weight:.4f}",
                f"{bucket.drift:.4f}",
            ]
        )
    writer.writerow(
        [
            "TOTAL",
            f"{status.total_value:.2f}",
            f"{status.total_cost:.2f}",
            f"{status.total_pnl:.2f}",
            f"{status.total_pnl_pct:.4f}",
            "",
            "",
            "",
        ]
    )
    return buffer.getvalue()


def _sparkline_svg(values: list[float]) -> str:
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    width, height = 280.0, 60.0
    step = width / (len(values) - 1)
    points = " ".join(
        f"{idx * step:.1f},{height - (value - low) / span * (height - 8) - 4:.1f}"
        for idx, value in enumerate(values)
    )
    return (
        "<svg viewBox='0 0 280 60' role='img' aria-label='Portfolio value history' style='width:100%;max-width:280px;'>"
        f"<polyline fill='none' stroke='#2563eb' stroke-width='2' points='{points}'/>"
        "</svg>"
    )


def _donut_svg(status: PortfolioStatus) -> str:
    colors = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#64748b", "#dc2626"]
    radius = 74
    circumference = 2 * 3.14159 * radius
    offset = 0.0
    circles: list[str] = []
    for idx, bucket in enumerate(status.buckets):
        dash = max(0.0, bucket.current_weight) / 100.0 * circumference
        circles.append(
            "<circle cx='100' cy='100' r='74' fill='none' "
            f"stroke='{colors[idx % len(colors)]}' stroke-width='26' "
            f"stroke-dasharray='{dash:.2f} {circumference - dash:.2f}' "
            f"stroke-dashoffset='{-offset:.2f}' transform='rotate(-90 100 100)' />"
        )
        offset += dash
    return (
        "<svg viewBox='0 0 200 200' role='img' aria-label='Current allocation donut'>"
        "<circle cx='100' cy='100' r='74' fill='none' stroke='#e5e7eb' stroke-width='26'/>"
        + "".join(circles)
        + f"<text x='100' y='96' text-anchor='middle' font-size='18'>{status.total_value:.0f}</text>"
        + f"<text x='100' y='118' text-anchor='middle' font-size='12'>{escape(status.base_ccy)}</text>"
        + "</svg>"
    )


def write_dashboard_html(
    status: PortfolioStatus, path: str, *, history: list[Snapshot] | None = None
) -> None:
    history = history or []
    history_section = ""
    if len(history) >= 2:
        first, last = history[0], history[-1]
        change = last.total_value - first.total_value
        change_pct = (change / first.total_value * 100.0) if first.total_value else 0.0
        spark = _sparkline_svg([snap.total_value for snap in history])
        history_section = (
            '<section class="history"><h2>Value history</h2>'
            f"{spark}"
            f'<p class="note">{len(history)} snapshots, {escape(first.as_of[:10])} to {escape(last.as_of[:10])}: {change:+.2f} ({change_pct:+.2f}%).</p>'
            "</section>"
        )
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(bucket.bucket)}</td>"
        f"<td>{bucket.market_value:.2f}</td>"
        f"<td>{bucket.cost_basis:.2f}</td>"
        f"<td>{bucket.pnl:.2f}</td>"
        f"<td>{bucket.pnl_pct:.2f}%</td>"
        f"<td>{bucket.current_weight:.2f}%</td>"
        f"<td>{bucket.target_weight:.2f}%</td>"
        f"<td><span class='bar'><i style='width:{min(abs(bucket.drift), 40) * 2.5:.1f}%;'></i></span>"
        f"{bucket.drift:.2f}%</td>"
        "</tr>"
        for bucket in status.buckets
    )
    stale = ", ".join(status.stale_prices) if status.stale_prices else "None"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Asset Allocator Dashboard</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; color: #111827; background: #f8fafc; }}
main {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px; }}
header {{ display: flex; gap: 24px; align-items: center; justify-content: space-between; border-bottom: 1px solid #d1d5db; padding-bottom: 20px; }}
h1 {{ margin: 0 0 8px; font-size: 30px; }}
.metric {{ display: inline-block; margin-right: 18px; font-weight: 700; }}
.grid {{ display: grid; grid-template-columns: 260px 1fr; gap: 28px; margin-top: 26px; align-items: start; }}
table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d1d5db; }}
th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ background: #eef2ff; font-size: 13px; }}
.bar {{ display: inline-block; width: 72px; height: 8px; margin-right: 8px; background: #e5e7eb; vertical-align: middle; }}
.bar i {{ display: block; height: 8px; background: #2563eb; }}
.note {{ margin-top: 18px; color: #475569; font-size: 14px; }}
.history {{ margin-top: 28px; border-top: 1px solid #d1d5db; padding-top: 16px; }}
.history h2 {{ font-size: 18px; margin: 0 0 10px; }}
@media (max-width: 760px) {{ header, .grid {{ display: block; }} svg {{ max-width: 220px; }} table {{ font-size: 13px; }} }}
</style>
</head>
<body>
<main>
<header>
<div>
<h1>Asset Allocator Dashboard</h1>
<div>As of {escape(status.as_of)}. Base currency: {escape(status.base_ccy)}.</div>
<p><span class="metric">Value {status.total_value:.2f}</span><span class="metric">P&amp;L {status.total_pnl:.2f} ({status.total_pnl_pct:.2f}%)</span></p>
</div>
</header>
<section class="grid">
<div>{_donut_svg(status)}</div>
<table>
<thead><tr><th>Bucket</th><th>Value</th><th>Cost</th><th>P&amp;L</th><th>P&amp;L %</th><th>Current</th><th>Target</th><th>Drift</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</section>
{history_section}
<p class="note">Stale prices: {escape(stale)}</p>
<p class="note">NOT FINANCIAL ADVICE. This dashboard displays arithmetic from user-supplied data and illustrative, user-tunable defaults.</p>
</main>
</body>
</html>
"""
    Path(path).write_text(html, encoding="utf-8")
