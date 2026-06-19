from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from asset_allocator.allocation import (
    custom_allocation,
    rebalance,
    split_amount,
    target_allocation,
)
from asset_allocator.config import ASSET_CLASSES, BASE_CCY, REBALANCE_BAND
from asset_allocator.contribute import plan_contribution
from asset_allocator.history import load_history, period_return, record_snapshot, render_history
from asset_allocator.holdings_io import import_into, parse_holdings_csv
from asset_allocator.models import Holding, RiskProfile, TargetAllocation
from asset_allocator.profile import run_questionnaire
from asset_allocator.projection import project
from asset_allocator.report import render_status, render_status_csv, write_dashboard_html
from asset_allocator.store import StoreError, add_holding, load, remove_holding, save
from asset_allocator.valuation import revalue

DISCLAIMER = (
    "NOT FINANCIAL ADVICE. Weights are illustrative, user-tunable defaults; "
    "this tool only computes math from user-supplied inputs."
)


def _empty_store() -> dict[str, Any]:
    return {"profile": None, "target": None, "holdings": [], "price_cache": {}, "history": []}


def _load_or_empty(path: str) -> dict[str, Any]:
    try:
        return load(path)
    except StoreError:
        return _empty_store()


def _read_json_file(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _profile_from_data(data: dict[str, Any]) -> RiskProfile:
    profile = data.get("profile")
    if not isinstance(profile, dict):
        raise StoreError("Store has no profile. Run 'allocate init --from-file ...' first.")
    return RiskProfile(**profile)


def _target_from_data(data: dict[str, Any]) -> TargetAllocation:
    target = data.get("target")
    if not isinstance(target, dict):
        raise StoreError(
            "Store has no target allocation. Run 'allocate init --from-file ...' first."
        )
    return TargetAllocation(**target)


def _status_from_data(data: dict[str, Any], *, refresh: bool) -> Any:
    target = _target_from_data(data)
    return revalue(
        data.get("holdings", []),
        target,
        as_of=datetime.now(UTC).isoformat(timespec="seconds"),
        base_ccy=BASE_CCY,
        refresh=refresh,
        cache=data.setdefault("price_cache", {}),
    )


def _print_target(target: TargetAllocation, amounts: dict[str, float] | None = None) -> None:
    print(DISCLAIMER)
    print(f"\nProfile: {target.profile_name}")
    print("Bucket          Target%      Amount")
    for bucket in ASSET_CLASSES:
        amount = "" if amounts is None else f"{amounts.get(bucket, 0.0):.2f}"
        print(f"{bucket:<12} {target.weights.get(bucket, 0.0):>8.2f} {amount:>11}")


def cmd_init(args: argparse.Namespace) -> int:
    answers = _read_json_file(args.from_file) if args.from_file else None
    profile = run_questionnaire(answers)
    target = target_allocation(profile, glide_path=args.glide_path)
    data = _load_or_empty(args.store)
    data["profile"] = asdict(profile)
    data["target"] = asdict(target)
    data.setdefault("holdings", [])
    data.setdefault("price_cache", {})
    save(data, args.store)
    _print_target(target)
    print(f"\nSaved store: {args.store}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    data = load(args.store)
    _profile_from_data(data)
    target = _target_from_data(data)
    amounts = split_amount(target, args.amount) if args.amount is not None else None
    if args.json:
        payload: dict[str, Any] = {"target": asdict(target), "disclaimer": DISCLAIMER}
        if amounts is not None:
            payload["amounts"] = amounts
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    _print_target(target, amounts)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    if args.bucket not in ASSET_CLASSES:
        raise StoreError(
            f"Unknown bucket {args.bucket!r}; expected one of {', '.join(ASSET_CLASSES)}."
        )
    holding = Holding(
        bucket=args.bucket,
        label=args.label,
        kind=args.kind,
        cost_basis=args.cost,
        quantity=args.quantity,
        ticker=args.ticker,
        apy=args.apy,
        opened=args.opened,
        valuation_override=args.override,
    )
    data = _load_or_empty(args.store)
    add_holding(data, holding)
    save(data, args.store)
    print(f"Added holding: {args.label}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    data = load(args.store)
    removed = remove_holding(data, args.label)
    save(data, args.store)
    print(f"Removed holding: {args.label}" if removed else f"No holding found: {args.label}")
    return 0 if removed else 1


def cmd_status(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=args.refresh)
    if args.refresh:
        save(data, args.store)
    if args.json:
        print(json.dumps(render_status(status, "dict"), indent=2, sort_keys=True))
    else:
        print(render_status(status, "text"))
    return 0


def cmd_rebalance(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=False)
    actions = rebalance(status, band=args.band)
    if args.json:
        print(json.dumps([asdict(action) for action in actions], indent=2, sort_keys=True))
    else:
        for action in actions:
            print(
                f"{action.bucket:<12} {action.direction:<5} "
                f"{action.amount:>10.2f} drift={action.drift:.2f}%"
            )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=args.refresh)
    if args.refresh:
        save(data, args.store)
    write_dashboard_html(status, args.html, history=load_history(data))
    print(f"Wrote dashboard: {args.html}")
    return 0


def cmd_contribute(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=args.refresh)
    if args.refresh:
        save(data, args.store)
    items = plan_contribution(status, args.amount)
    if args.json:
        print(json.dumps([asdict(item) for item in items], indent=2, sort_keys=True))
        return 0
    print(DISCLAIMER)
    print(f"\nContribution plan for {args.amount:.2f} {status.base_ccy} (buy-only)")
    print("Bucket            Buy   Current%  Projected%   Target%")
    for item in items:
        print(
            f"{item.bucket:<12} {item.amount:>9.2f} {item.current_weight:>9.2f} "
            f"{item.projected_weight:>11.2f} {item.target_weight:>9.2f}"
        )
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=args.refresh)
    snapshot = record_snapshot(data, status, note=args.note or "")
    save(data, args.store)
    print(f"Recorded snapshot as of {snapshot.as_of}: {snapshot.total_value:.2f} {status.base_ccy}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    data = load(args.store)
    if args.json:
        summary = period_return(data)
        payload = {
            "history": [asdict(snap) for snap in load_history(data)],
            "period_return": asdict(summary) if summary is not None else None,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(render_history(data))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    data = load(args.store)
    status = _status_from_data(data, refresh=args.refresh)
    if args.refresh:
        save(data, args.store)
    if args.format == "csv":
        output = render_status_csv(status)
    elif args.format == "md":
        output = str(render_status(status, "md"))
    else:
        output = json.dumps(render_status(status, "dict"), indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as handle:
            handle.write(output if output.endswith("\n") else output + "\n")
        print(f"Wrote {args.format}: {args.out}")
    else:
        print(output)
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    with open(args.csv, encoding="utf-8") as handle:
        holdings = parse_holdings_csv(handle.read())
    data = _load_or_empty(args.store)
    count = import_into(data, holdings, replace=args.replace)
    save(data, args.store)
    verb = "Replaced store with" if args.replace else "Imported"
    print(f"{verb} {count} holding(s) into {args.store}")
    return 0


def _parse_weight_args(pairs: list[str]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for pair in pairs:
        bucket, sep, raw = pair.partition("=")
        if not sep:
            raise ValueError(f"--weight expects BUCKET=NN, got {pair!r}.")
        weights[bucket.strip()] = float(raw)
    return weights


def cmd_set_target(args: argparse.Namespace) -> int:
    if args.from_file:
        payload = _read_json_file(args.from_file)
        weights = {str(key): float(value) for key, value in payload.items()}
    else:
        weights = _parse_weight_args(args.weight or [])
    if not weights:
        raise ValueError("Provide --from-file or at least one --weight BUCKET=NN.")
    target = custom_allocation(weights)
    data = _load_or_empty(args.store)
    data["target"] = asdict(target)
    data.setdefault("holdings", [])
    data.setdefault("price_cache", {})
    data.setdefault("history", [])
    save(data, args.store)
    _print_target(target)
    print(f"\nSaved custom target: {args.store}")
    return 0


def cmd_project(args: argparse.Namespace) -> int:
    initial = args.initial
    if initial is None:
        try:
            initial = _status_from_data(load(args.store), refresh=False).total_value
        except StoreError:
            initial = 0.0
    rows = project(
        initial, args.monthly, args.annual_return, args.years, inflation_pct=args.inflation
    )
    if args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True))
        return 0
    print(DISCLAIMER)
    print(
        f"\nProjection: start {initial:.2f} {BASE_CCY}, +{args.monthly:.2f}/mo, "
        f"{args.annual_return:.2f}%/yr nominal, {args.inflation:.2f}% inflation"
    )
    print("Year   Contributed       Nominal          Real        Growth")
    for row in rows:
        print(
            f"{row.year:>4} {row.contributed:>13.2f} {row.nominal:>13.2f} "
            f"{row.real:>13.2f} {row.growth:>13.2f}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="allocate", description="Keyless asset allocation CLI.")
    parser.add_argument("--version", action="version", version="asset-allocator 0.3.0")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Run the risk questionnaire and write profile + target.")
    init.add_argument("--from-file", help="JSON answers file for non-interactive runs.")
    init.add_argument("--glide-path", action="store_true", help="Tilt equity by age glide path.")
    init.add_argument("--store", default="./portfolio.json")
    init.set_defaults(func=cmd_init)

    plan = sub.add_parser("plan", help="Show target allocation and optional money split.")
    plan.add_argument("--amount", type=float)
    plan.add_argument("--json", action="store_true")
    plan.add_argument("--store", default="./portfolio.json")
    plan.set_defaults(func=cmd_plan)

    add = sub.add_parser("add", help="Add a holding.")
    add.add_argument("--bucket", required=True)
    add.add_argument("--label", required=True)
    add.add_argument("--kind", choices=["market", "accrual", "static"], required=True)
    add.add_argument("--ticker")
    add.add_argument("--quantity", type=float, default=0.0)
    add.add_argument("--cost", type=float, required=True)
    add.add_argument("--apy", type=float, default=0.0)
    add.add_argument("--opened")
    add.add_argument("--override", type=float)
    add.add_argument("--store", default="./portfolio.json")
    add.set_defaults(func=cmd_add)

    remove = sub.add_parser("remove", help="Remove a holding by label.")
    remove.add_argument("--label", required=True)
    remove.add_argument("--store", default="./portfolio.json")
    remove.set_defaults(func=cmd_remove)

    status = sub.add_parser("status", help="Show daily P&L and drift.")
    status_refresh = status.add_mutually_exclusive_group()
    status_refresh.add_argument("--refresh", dest="refresh", action="store_true", default=True)
    status_refresh.add_argument("--no-refresh", dest="refresh", action="store_false")
    status.add_argument("--json", action="store_true")
    status.add_argument("--store", default="./portfolio.json")
    status.set_defaults(func=cmd_status)

    rb = sub.add_parser("rebalance", help="Show buy/sell/hold suggestions.")
    rb.add_argument("--band", type=float, default=REBALANCE_BAND)
    rb.add_argument("--json", action="store_true")
    rb.add_argument("--store", default="./portfolio.json")
    rb.set_defaults(func=cmd_rebalance)

    report = sub.add_parser("report", help="Write a self-contained HTML dashboard.")
    report.add_argument("--html", required=True)
    report_refresh = report.add_mutually_exclusive_group()
    report_refresh.add_argument("--refresh", dest="refresh", action="store_true", default=True)
    report_refresh.add_argument("--no-refresh", dest="refresh", action="store_false")
    report.add_argument("--store", default="./portfolio.json")
    report.set_defaults(func=cmd_report)

    contribute = sub.add_parser(
        "contribute", help="Plan a buy-only cash contribution toward target weights."
    )
    contribute.add_argument("--amount", type=float, required=True)
    contribute.add_argument("--json", action="store_true")
    contribute_refresh = contribute.add_mutually_exclusive_group()
    contribute_refresh.add_argument("--refresh", dest="refresh", action="store_true", default=True)
    contribute_refresh.add_argument("--no-refresh", dest="refresh", action="store_false")
    contribute.add_argument("--store", default="./portfolio.json")
    contribute.set_defaults(func=cmd_contribute)

    snapshot = sub.add_parser("snapshot", help="Record the current status into the history log.")
    snapshot.add_argument("--note", default="")
    snapshot_refresh = snapshot.add_mutually_exclusive_group()
    snapshot_refresh.add_argument("--refresh", dest="refresh", action="store_true", default=True)
    snapshot_refresh.add_argument("--no-refresh", dest="refresh", action="store_false")
    snapshot.add_argument("--store", default="./portfolio.json")
    snapshot.set_defaults(func=cmd_snapshot)

    history = sub.add_parser("history", help="Show recorded snapshots and period return.")
    history.add_argument("--json", action="store_true")
    history.add_argument("--store", default="./portfolio.json")
    history.set_defaults(func=cmd_history)

    export = sub.add_parser("export", help="Export the current status as CSV, Markdown, or JSON.")
    export.add_argument("--format", choices=["csv", "md", "json"], default="csv")
    export.add_argument("--out", help="Output file; prints to stdout if omitted.")
    export_refresh = export.add_mutually_exclusive_group()
    export_refresh.add_argument("--refresh", dest="refresh", action="store_true", default=True)
    export_refresh.add_argument("--no-refresh", dest="refresh", action="store_false")
    export.add_argument("--store", default="./portfolio.json")
    export.set_defaults(func=cmd_export)

    import_p = sub.add_parser("import", help="Import holdings from a CSV file (inverse of export).")
    import_p.add_argument("--csv", required=True, help="CSV file with holding rows.")
    import_p.add_argument("--replace", action="store_true", help="Replace existing holdings.")
    import_p.add_argument("--store", default="./portfolio.json")
    import_p.set_defaults(func=cmd_import)

    set_target = sub.add_parser(
        "set-target", help="Set a custom target allocation, overriding the model template."
    )
    set_target.add_argument("--from-file", help="JSON object of bucket -> weight.")
    set_target.add_argument(
        "--weight",
        action="append",
        metavar="BUCKET=NN",
        help="Repeatable, e.g. --weight equity=50.",
    )
    set_target.add_argument("--store", default="./portfolio.json")
    set_target.set_defaults(func=cmd_set_target)

    project_p = sub.add_parser(
        "project", help="Project compound growth from contributions (illustrative, not advice)."
    )
    project_p.add_argument("--years", type=int, required=True)
    project_p.add_argument("--monthly", type=float, default=0.0)
    project_p.add_argument("--annual-return", type=float, default=7.0, dest="annual_return")
    project_p.add_argument(
        "--initial", type=float, help="Start value; defaults to the current portfolio value."
    )
    project_p.add_argument("--inflation", type=float, default=0.0)
    project_p.add_argument("--json", action="store_true")
    project_p.add_argument("--store", default="./portfolio.json")
    project_p.set_defaults(func=cmd_project)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (StoreError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
