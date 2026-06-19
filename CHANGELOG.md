# Changelog

## 0.5.0 - 2026-06-19

- Added a cash-flow / budget module persisted in the store: income and expense items
  (monthly or yearly), with `allocate income add|list|rm`, `allocate expense add|list|rm`,
  and `allocate budget` (summary) / `allocate budget --import-csv FILE` (bulk load).
- The summary auto-computes monthly income, monthly expense (yearly items normalized),
  monthly surplus, savings rate, and annual figures.
- The dashboard now renders a Cash flow panel (income/mo, expense/mo, surplus, savings
  rate, and a liquid-runway estimate) when the store has budget items — fully localized.
- Everything stays keyless, offline, and deterministic; budget data lives in the same JSON
  store, so editing it and re-running `report` updates the dashboard.

## 0.4.0 - 2026-06-19

- Redesigned the HTML dashboard: KPI summary cards (net worth, total P&L, total cost,
  largest bucket), a donut + legend, a color-coded allocation table with drift bars, and a
  cleaner, card-based responsive layout.
- Added dashboard localization: `allocate report --lang en|vi` renders the whole dashboard
  in English or Vietnamese (new `i18n` module; bucket names and UI strings translated).
- Added locale-aware money formatting with thousands grouping (`format_money`): Vietnamese
  uses `.`/`,` and English uses `,`/`.`.
- The dashboard stays a single self-contained offline HTML file (no CDN, no scripts).

## 0.3.0 - 2026-06-19

- Added `allocate import --csv FILE [--replace]`: load holdings in bulk from a CSV (the
  inverse of `allocate export`), with per-row validation and a clear error per bad row.
- Added `allocate set-target`: define a custom target allocation with `--weight bucket=NN`
  (repeatable) or `--from-file weights.json`, re-normalized to 100% — no longer limited to
  the four built-in risk models.
- Added `allocate project --years N [--monthly M] [--annual-return R] [--inflation I]`: an
  illustrative compound-growth projection (nominal, inflation-adjusted real, and growth)
  for contribution planning. Deterministic; not a forecast.
- Added `examples/sample_holdings.csv` for the import quickstart.
- All new features stay keyless, offline, and deterministic, with network-free tests.

## 0.2.0 - 2026-06-19

- Added `allocate contribute --amount N`: a buy-only DCA / cash-flow plan that splits a fresh
  contribution toward target weights without selling (fills the most underweight buckets first).
- Added `allocate snapshot` and `allocate history`: record point-in-time portfolio snapshots into
  the store and review the value series plus a simple period return.
- Added `allocate export --format csv|md|json`: export the current bucket status to a file or stdout.
- The HTML dashboard now embeds an inline-SVG value-history sparkline when snapshots exist.
- All new features stay keyless, offline, and deterministic, with network-free tests.

## 0.1.0 - 2026-06-12

- Initial keyless CLI for risk questionnaire based target allocation.
- Added daily bucket valuation, drift tracking, rebalance suggestions, and offline HTML dashboard.
- Added fictional examples, network-free tests, and CI for Windows and Ubuntu.
