<div align="center">

# asset-allocator

Turn a 2-minute risk quiz into a target asset allocation, then track daily P&L and drift - keyless, offline-friendly.

[![CI](https://github.com/baronguyen001/asset-allocator/actions/workflows/ci.yml/badge.svg)](https://github.com/baronguyen001/asset-allocator/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PyPI](https://img.shields.io/badge/pypi-asset--allocator-lightgrey)

</div>

> NOT FINANCIAL ADVICE. `asset-allocator` uses illustrative, user-tunable defaults to compute allocation math from your inputs. It does not recommend securities, does not execute trades, and does not know your full financial situation.

`asset-allocator` is a keyless CLI and self-contained HTML dashboard for simple portfolio planning. It asks a small risk-appetite questionnaire, maps the answers to one of four illustrative model templates, plans buy-only contributions toward those targets, tracks daily P&L and snapshot history, and flags allocation drift for rebalancing.

## 30-second quickstart

```bash
# PyPI release pending — install from source (the quickstart uses the bundled examples):
git clone https://github.com/baronguyen001/asset-allocator
cd asset-allocator
pip install -e .

allocate init --from-file examples/sample_answers.json
allocate plan --amount 100000
allocate status --no-refresh --store examples/sample_portfolio.json
allocate report --html dashboard.html --no-refresh --store examples/sample_portfolio.json
```

The bundled examples are fictional and include cached demo prices, so the quickstart needs no network and no API keys.

Example console output:

```text
Portfolio status as of 2026-06-12T00:00:00+00:00
Total value: 101500.00 USD
Total P&L: 1500.00 (1.50%)

Bucket          Value       P&L    P&L%  Current  Target   Drift
equity         40500.00   1500.00    3.85    39.90   40.00   -0.10
bonds          25000.00      0.00    0.00    24.63   25.00   -0.37
gold           10200.00    200.00    2.00    10.05   10.00    0.05
```

The HTML dashboard is a single offline file with inline CSS and SVG. It has no CDN, no scripts, and no external assets.

## Features

| Feature | What ships |
|---|---|
| 7 buckets | equity, bonds, gold, real estate, savings, cash, emergency reserve |
| 4 model templates | conservative, balanced, growth, aggressive |
| Custom targets | define your own per-bucket weights, re-normalized to 100% |
| Glide path | optional age-based equity tilt |
| Drift tracking | current weight vs target weight by bucket |
| Rebalance plan | buy, sell, or hold suggestions by bucket |
| DCA contribution plan | buy-only split of a fresh deposit toward target weights |
| Cash-flow / budget | track income & expense items (monthly/yearly) → surplus, savings rate, liquid runway |
| Goal tracking | milestone-year net-worth targets → progress, gap, years left, required return |
| Growth projection | illustrative compound-growth forecast (nominal + real) for planning |
| Snapshot history | record point-in-time snapshots and review period return |
| CSV import / export | bulk-load holdings/budget from a sheet; dump status to CSV/Markdown/JSON |
| Keyless prices | Stooq CSV for market symbols, CoinGecko JSON for `crypto:<id>` |
| Static dashboard | KPI cards, donut + legend, color-coded table, cash-flow panel, value-history sparkline |
| Local web app | `allocate serve` — editable detail tables, emoji icons, interactive charts, save-to-store |
| Localized (en/vi) | English or Vietnamese (`--lang en\|vi`), locale-aware number formatting |
| Offline | static report is a single HTML file; the web app bundles Chart.js and binds to localhost |

## How the allocation model works

The questionnaire scores horizon, drawdown tolerance, income stability, emergency-fund months, and liquidity needs on a 0-100 scale. That score maps to one of four model templates:

- `conservative`
- `balanced`
- `growth`
- `aggressive`

Those templates are illustrative defaults and are meant to be edited for your own use. Passing `--glide-path` adjusts the equity weight toward `110 - age`, capped to a conservative range around the selected template, then re-normalizes all buckets to 100%. If none of the templates fit, `allocate set-target` lets you set your own per-bucket weights directly (they are re-normalized to 100%).

## CLI

```bash
allocate init --from-file examples/sample_answers.json --glide-path
allocate plan --amount 100000 --json
allocate add --bucket equity --label "Demo Equity Fund" --kind market --ticker demo.us --quantity 10 --cost 3000
allocate remove --label "Demo Equity Fund"
allocate status --no-refresh --store examples/sample_portfolio.json
allocate import --csv examples/sample_holdings.csv --replace --store examples/sample_portfolio.json
allocate set-target --weight equity=60 --weight bonds=25 --weight gold=15 --store examples/sample_portfolio.json
allocate contribute --amount 5000 --no-refresh --store examples/sample_portfolio.json
allocate rebalance --json --store examples/sample_portfolio.json
allocate snapshot --note "monthly check-in" --no-refresh --store examples/sample_portfolio.json
allocate history --store examples/sample_portfolio.json
allocate export --format csv --out status.csv --no-refresh --store examples/sample_portfolio.json
allocate income add --label "Salary" --amount 80 --store examples/sample_portfolio.json
allocate expense add --label "Food" --amount 8 --store examples/sample_portfolio.json
allocate expense add --label "Insurance" --amount 60 --freq yearly --category protection --store examples/sample_portfolio.json
allocate budget --store examples/sample_portfolio.json            # income/expense/surplus summary
allocate budget --import-csv my_budget.csv --replace --store examples/sample_portfolio.json
allocate project --years 20 --monthly 500 --annual-return 7 --inflation 3
allocate goal add --year 2032 --label "Financial freedom" --target 155000 --store examples/sample_portfolio.json
allocate report --html dashboard.html --lang en --no-refresh --store examples/sample_portfolio.json
allocate report --html bang-dieu-khien.html --lang vi --no-refresh --store examples/sample_portfolio.json
allocate serve --lang vi --store examples/sample_portfolio.json   # interactive editable web app
```

`contribute` plans a fresh deposit buy-only: it never suggests selling, just routes new cash to the most underweight buckets first, which is the usual monthly-DCA workflow. `rebalance`, by contrast, assumes you can both buy and sell. `import` bulk-loads holdings from a CSV (the inverse of `export`), and `set-target` lets you define your own per-bucket weights instead of using a model template. `income`/`expense`/`budget` track your cash flow in the same store: each item is monthly or yearly, and `budget` normalizes everything to a monthly view (income, expense, surplus, savings rate). `goal` records milestone-year net-worth targets (e.g. a number to hit by 2032/2042) and the dashboards show progress toward them. `snapshot` appends the current totals so `history` can show how the portfolio moved over time. `project` is an illustrative compound-growth planner (nominal + inflation-adjusted real) — deterministic arithmetic on your assumptions, not a forecast.

`python -m asset_allocator ...` works the same as `allocate ...`.

## Web app (`allocate serve`)

For an interactive view, install the optional extra and run the local server:

```bash
pip install "asset-allocator[web]"
allocate serve --lang vi --store portfolio.json   # opens http://127.0.0.1:8765
```

It serves a single-user, localhost-only page with editable detail tables for income, expenses, and holdings (emoji category icons), interactive charts (expense by category, income vs expense, a savings-rate gauge, and a net-worth-vs-goals trajectory), and a Goals progress panel. Edit a cell, click **Save**, and changes are written straight back to the JSON store. Chart.js is vendored locally, so the app runs fully offline and calls no external API.

## Price sources

No keys are required. Market holdings use Stooq's public CSV endpoint. Crypto holdings use CoinGecko's public simple-price endpoint via ticker strings like `crypto:bitcoin`. If a refresh fails and a cached price exists, the valuation continues and marks that ticker stale.

## FAQ

**Is this financial advice?** No. It is arithmetic on user-supplied inputs using illustrative defaults.

**Do I need API keys or a brokerage account?** No. The repo is keyless and has no broker integrations.

**Does it trade or rebalance for me?** No. It only prints bucket-level drift math.

**Want the always-on bot version?** Trawlkit is the commercial direction for a Telegram or Discord workflow that runs the quiz, pushes daily P&L, and pings on drift.

Related OSS siblings: `dex-chart-dashboard`, `walk-forward-validator`, and `confluence-scanner`. For a broader skill path, see `ai-automation-skills`.

## Development

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src/asset_allocator
pytest --cov=asset_allocator --cov-fail-under=70
```

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=baronguyen001/asset-allocator&type=Date)](https://star-history.com/#baronguyen001/asset-allocator&Date)

## License

MIT (c) 2026 baronguyen001.
