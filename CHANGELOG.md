# Changelog

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
