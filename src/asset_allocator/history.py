"""Point-in-time portfolio snapshots and simple period-return math.

NOT FINANCIAL ADVICE. Snapshots are arithmetic over user-supplied holdings. Period return
is a plain value-to-value comparison that ignores external cash flows; it is not a
performance attribution, a benchmark comparison, or advice.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from asset_allocator.models import PeriodReturn, PortfolioStatus, Snapshot


def _history_list(data: dict[str, Any]) -> list[Any]:
    history = data.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("Portfolio store field 'history' must be a list.")
    return history


def record_snapshot(data: dict[str, Any], status: PortfolioStatus, note: str = "") -> Snapshot:
    """Append a snapshot of the current status to the store's history list."""
    snapshot = Snapshot(
        as_of=status.as_of,
        total_value=status.total_value,
        total_cost=status.total_cost,
        total_pnl=status.total_pnl,
        total_pnl_pct=status.total_pnl_pct,
        weights={bucket.bucket: bucket.current_weight for bucket in status.buckets},
        note=note,
    )
    _history_list(data).append(asdict(snapshot))
    return snapshot


def load_history(data: dict[str, Any]) -> list[Snapshot]:
    """Parse stored snapshot dicts into Snapshot objects, skipping malformed entries."""
    snapshots: list[Snapshot] = []
    for entry in _history_list(data):
        if not isinstance(entry, dict) or "as_of" not in entry:
            continue
        weights = entry.get("weights", {})
        weights = weights if isinstance(weights, dict) else {}
        snapshots.append(
            Snapshot(
                as_of=str(entry.get("as_of", "")),
                total_value=float(entry.get("total_value", 0.0)),
                total_cost=float(entry.get("total_cost", 0.0)),
                total_pnl=float(entry.get("total_pnl", 0.0)),
                total_pnl_pct=float(entry.get("total_pnl_pct", 0.0)),
                weights={str(key): float(value) for key, value in weights.items()},
                note=str(entry.get("note", "")),
            )
        )
    return snapshots


def period_return(data: dict[str, Any]) -> PeriodReturn | None:
    """Compare the first and last snapshot (and the last step), or None if fewer than two."""
    snapshots = load_history(data)
    if len(snapshots) < 2:
        return None
    first, prev, last = snapshots[0], snapshots[-2], snapshots[-1]
    change = round(last.total_value - first.total_value, 2)
    change_pct = round((change / first.total_value * 100.0) if first.total_value else 0.0, 4)
    last_change = round(last.total_value - prev.total_value, 2)
    last_pct = round((last_change / prev.total_value * 100.0) if prev.total_value else 0.0, 4)
    return PeriodReturn(
        start=first.as_of,
        end=last.as_of,
        start_value=first.total_value,
        end_value=last.total_value,
        change=change,
        change_pct=change_pct,
        last_change=last_change,
        last_change_pct=last_pct,
        snapshots=len(snapshots),
    )


def render_history(data: dict[str, Any]) -> str:
    """Render the snapshot series and period return as a fixed-width text table."""
    snapshots = load_history(data)
    if not snapshots:
        return "No snapshots recorded yet. Run 'allocate snapshot' to record one."
    lines = ["Date                       Value        P&L     P&L%  Note"]
    for snap in snapshots:
        lines.append(
            f"{snap.as_of:<26} {snap.total_value:>10.2f} {snap.total_pnl:>10.2f} "
            f"{snap.total_pnl_pct:>7.2f}  {snap.note}".rstrip()
        )
    summary = period_return(data)
    if summary is not None:
        lines.append("")
        lines.append(
            f"Period {summary.start[:10]} -> {summary.end[:10]} over {summary.snapshots} "
            f"snapshots: {summary.change:+.2f} ({summary.change_pct:+.2f}%); "
            f"last step {summary.last_change:+.2f} ({summary.last_change_pct:+.2f}%)."
        )
    return "\n".join(lines)
