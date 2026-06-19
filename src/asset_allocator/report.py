# ruff: noqa: E501
from __future__ import annotations

import csv
import io
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from asset_allocator.i18n import bucket_label, normalize_lang, t
from asset_allocator.models import PortfolioStatus, Snapshot

_BUCKET_COLORS = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#64748b", "#dc2626"]


def format_money(value: float, currency: str = "", lang: str = "en") -> str:
    """Format a number with locale-aware thousands grouping (vi uses '.', en uses ',')."""
    thousands = "." if lang == "vi" else ","
    decimal = "," if lang == "vi" else "."
    negative = value < 0
    magnitude = abs(value)
    integer = int(magnitude)
    fraction = int(round((magnitude - integer) * 100))
    if fraction >= 100:
        integer += 1
        fraction -= 100
    int_str = f"{integer:,}".replace(",", thousands)
    out = int_str if fraction == 0 else f"{int_str}{decimal}{fraction:02d}"
    if negative:
        out = f"-{out}"
    return f"{out} {currency}".strip() if currency else out


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


def _donut_svg(status: PortfolioStatus, center_value: str, center_label: str) -> str:
    radius = 74
    circumference = 2 * 3.14159 * radius
    offset = 0.0
    circles: list[str] = []
    for idx, bucket in enumerate(status.buckets):
        dash = max(0.0, bucket.current_weight) / 100.0 * circumference
        circles.append(
            "<circle cx='100' cy='100' r='74' fill='none' "
            f"stroke='{_BUCKET_COLORS[idx % len(_BUCKET_COLORS)]}' stroke-width='26' "
            f"stroke-dasharray='{dash:.2f} {circumference - dash:.2f}' "
            f"stroke-dashoffset='{-offset:.2f}' transform='rotate(-90 100 100)' />"
        )
        offset += dash
    return (
        "<svg viewBox='0 0 200 200' role='img' aria-label='Allocation donut'>"
        "<circle cx='100' cy='100' r='74' fill='none' stroke='#e5e7eb' stroke-width='26'/>"
        + "".join(circles)
        + f"<text x='100' y='95' text-anchor='middle' font-size='11' fill='#64748b'>{escape(center_label)}</text>"
        + f"<text x='100' y='116' text-anchor='middle' font-size='17' font-weight='700' fill='#0f172a'>{escape(center_value)}</text>"
        + "</svg>"
    )


def _pnl_class(value: float) -> str:
    return "up" if value > 0 else "down" if value < 0 else "flat"


def write_dashboard_html(
    status: PortfolioStatus,
    path: str,
    *,
    history: list[Snapshot] | None = None,
    lang: str = "en",
    currency: str | None = None,
) -> None:
    lang = normalize_lang(lang)
    ccy = currency or status.base_ccy
    history = history or []

    def money(value: float) -> str:
        return format_money(value, ccy, lang)

    def pct(value: float) -> str:
        text = f"{value:.2f}".replace(".", "," if lang == "vi" else ".")
        return f"{text}%"

    def signed_pct(value: float) -> str:
        sign = "+" if value > 0 else ""
        return f"{sign}{pct(value)}"

    funded = [b for b in status.buckets if b.market_value or b.current_weight]
    largest = max(status.buckets, key=lambda b: b.current_weight, default=None)
    largest_text = (
        f"{escape(bucket_label(lang, largest.bucket))} · {pct(largest.current_weight)}"
        if largest is not None
        else "-"
    )
    pnl_cls = _pnl_class(status.total_pnl)

    cards = (
        f'<div class="card"><div class="card-k">{escape(t(lang, "net_worth"))}</div>'
        f'<div class="card-v">{escape(money(status.total_value))}</div></div>'
        f'<div class="card"><div class="card-k">{escape(t(lang, "total_pnl"))}</div>'
        f'<div class="card-v {pnl_cls}">{escape(money(status.total_pnl))} '
        f'<span class="card-sub">({signed_pct(status.total_pnl_pct)})</span></div></div>'
        f'<div class="card"><div class="card-k">{escape(t(lang, "invested"))}</div>'
        f'<div class="card-v">{escape(money(status.total_cost))}</div></div>'
        f'<div class="card"><div class="card-k">{escape(t(lang, "largest_bucket"))}</div>'
        f'<div class="card-v">{largest_text}</div></div>'
    )

    legend = "\n".join(
        '<li><span class="dot" style="background:'
        f'{_BUCKET_COLORS[idx % len(_BUCKET_COLORS)]}"></span>'
        f'<span class="lg-name">{escape(bucket_label(lang, bucket.bucket))}</span>'
        f'<span class="lg-pct">{pct(bucket.current_weight)}</span>'
        f'<span class="lg-val">{escape(money(bucket.market_value))}</span></li>'
        for idx, bucket in enumerate(status.buckets)
    )

    rows = "\n".join(
        "<tr>"
        f"<td>{escape(bucket_label(lang, bucket.bucket))}</td>"
        f"<td>{escape(money(bucket.market_value))}</td>"
        f"<td>{escape(money(bucket.cost_basis))}</td>"
        f'<td class="{_pnl_class(bucket.pnl)}">{escape(money(bucket.pnl))}</td>'
        f'<td class="{_pnl_class(bucket.pnl)}">{signed_pct(bucket.pnl_pct)}</td>'
        f"<td>{pct(bucket.current_weight)}</td>"
        f"<td>{pct(bucket.target_weight)}</td>"
        f'<td class="drift"><span class="bar {_pnl_class(-abs(bucket.drift))}"><i style="width:{min(abs(bucket.drift), 40) * 2.5:.1f}%;"></i></span>'
        f"{signed_pct(bucket.drift)}</td>"
        "</tr>"
        for bucket in status.buckets
    )

    history_section = ""
    if len(history) >= 2:
        first, last = history[0], history[-1]
        change = last.total_value - first.total_value
        change_pct = (change / first.total_value * 100.0) if first.total_value else 0.0
        spark = _sparkline_svg([snap.total_value for snap in history])
        history_section = (
            f'<section class="panel history"><h2>{escape(t(lang, "value_history"))}</h2>'
            f"{spark}"
            f'<p class="note">{len(history)} {escape(t(lang, "snapshots"))}, {escape(first.as_of[:10])} → {escape(last.as_of[:10])}: '
            f'<span class="{_pnl_class(change)}">{escape(money(change))} ({signed_pct(change_pct)})</span>.</p>'
            "</section>"
        )

    stale = ", ".join(status.stale_prices) if status.stale_prices else t(lang, "none")
    donut = _donut_svg(status, money(status.total_value), t(lang, "net_worth"))
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(t(lang, "title"))}</title>
<style>
:root {{ --bg:#f1f5f9; --panel:#ffffff; --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --accent:#4f46e5; --up:#16a34a; --down:#dc2626; }}
* {{ box-sizing: border-box; }}
body {{ font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; margin: 0; color: var(--ink); background: var(--bg); }}
.bar-top {{ height: 5px; background: linear-gradient(90deg, #4f46e5, #06b6d4, #16a34a); }}
main {{ max-width: 1080px; margin: 0 auto; padding: 28px 20px 48px; }}
header {{ display: flex; gap: 16px; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; }}
h1 {{ margin: 0; font-size: 26px; letter-spacing: -0.02em; }}
.sub {{ color: var(--muted); font-size: 14px; margin-top: 4px; }}
.meta {{ color: var(--muted); font-size: 13px; text-align: right; }}
.cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 22px 0; }}
.card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }}
.card-k {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
.card-v {{ font-size: 22px; font-weight: 700; margin-top: 6px; }}
.card-sub {{ font-size: 14px; font-weight: 600; }}
.panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }}
.grid {{ display: grid; grid-template-columns: 300px 1fr; gap: 20px; align-items: start; }}
h2 {{ font-size: 16px; margin: 0 0 14px; }}
.donut-wrap {{ display: flex; flex-direction: column; align-items: center; gap: 12px; }}
svg {{ width: 100%; max-width: 240px; }}
ul.legend {{ list-style: none; margin: 0; padding: 0; width: 100%; }}
ul.legend li {{ display: grid; grid-template-columns: 14px 1fr auto auto; gap: 10px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 13px; }}
.dot {{ width: 11px; height: 11px; border-radius: 3px; }}
.lg-pct {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
.lg-val {{ font-weight: 600; font-variant-numeric: tabular-nums; }}
table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 11px 10px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--muted); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }}
tbody tr:hover {{ background: #f8fafc; }}
.up {{ color: var(--up); }}
.down {{ color: var(--down); }}
.flat {{ color: var(--muted); }}
.drift {{ display: flex; align-items: center; justify-content: flex-end; gap: 8px; }}
.bar {{ display: inline-block; width: 70px; height: 7px; border-radius: 4px; background: #eef2f7; }}
.bar i {{ display: block; height: 7px; border-radius: 4px; background: var(--accent); }}
.bar.down i {{ background: var(--down); }}
.note {{ color: var(--muted); font-size: 13px; margin: 14px 0 0; }}
.disclaimer {{ margin-top: 22px; padding: 12px 16px; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px; color: #9a3412; font-size: 13px; }}
@media (max-width: 820px) {{ .cards {{ grid-template-columns: repeat(2, 1fr); }} .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="bar-top"></div>
<main>
<header>
<div><h1>{escape(t(lang, "title"))}</h1><div class="sub">{escape(t(lang, "subtitle"))}</div></div>
<div class="meta">{escape(t(lang, "as_of"))}: {escape(status.as_of[:19])}<br>{escape(t(lang, "currency"))}: {escape(ccy)} · {len(funded)}/{len(status.buckets)} {escape(t(lang, "col_bucket"))}</div>
</header>
<section class="cards">{cards}</section>
<section class="grid">
<div class="panel donut-wrap">{donut}<ul class="legend">{legend}</ul></div>
<div class="panel">
<h2>{escape(t(lang, "allocation"))}</h2>
<table>
<thead><tr><th>{escape(t(lang, "col_bucket"))}</th><th>{escape(t(lang, "col_value"))}</th><th>{escape(t(lang, "col_cost"))}</th><th>{escape(t(lang, "col_pnl"))}</th><th>{escape(t(lang, "col_pnl_pct"))}</th><th>{escape(t(lang, "col_current"))}</th><th>{escape(t(lang, "col_target"))}</th><th>{escape(t(lang, "col_drift"))}</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p class="note">{escape(t(lang, "stale_prices"))}: {escape(stale)}</p>
</div>
</section>
{history_section}
<p class="disclaimer">{escape(t(lang, "disclaimer"))}</p>
</main>
</body>
</html>
"""
    Path(path).write_text(html, encoding="utf-8")
