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
| Glide path | optional age-based equity tilt |
| Drift tracking | current weight vs target weight by bucket |
| Rebalance plan | buy, sell, or hold suggestions by bucket |
| DCA contribution plan | buy-only split of a fresh deposit toward target weights |
| Snapshot history | record point-in-time snapshots and review period return |
| Export | dump the current status to CSV, Markdown, or JSON |
| Keyless prices | Stooq CSV for market symbols, CoinGecko JSON for `crypto:<id>` |
| Offline dashboard | self-contained HTML report with inline SVG + value-history sparkline |

## How the allocation model works

The questionnaire scores horizon, drawdown tolerance, income stability, emergency-fund months, and liquidity needs on a 0-100 scale. That score maps to one of four model templates:

- `conservative`
- `balanced`
- `growth`
- `aggressive`

Those templates are illustrative defaults and are meant to be edited for your own use. Passing `--glide-path` adjusts the equity weight toward `110 - age`, capped to a conservative range around the selected template, then re-normalizes all buckets to 100%.

## CLI

```bash
allocate init --from-file examples/sample_answers.json --glide-path
allocate plan --amount 100000 --json
allocate add --bucket equity --label "Demo Equity Fund" --kind market --ticker demo.us --quantity 10 --cost 3000
allocate remove --label "Demo Equity Fund"
allocate status --no-refresh --store examples/sample_portfolio.json
allocate contribute --amount 5000 --no-refresh --store examples/sample_portfolio.json
allocate rebalance --json --store examples/sample_portfolio.json
allocate snapshot --note "monthly check-in" --no-refresh --store examples/sample_portfolio.json
allocate history --store examples/sample_portfolio.json
allocate export --format csv --out status.csv --no-refresh --store examples/sample_portfolio.json
allocate report --html dashboard.html --no-refresh --store examples/sample_portfolio.json
```

`contribute` plans a fresh deposit buy-only: it never suggests selling, just routes new cash to the most underweight buckets first, which is the usual monthly-DCA workflow. `rebalance`, by contrast, assumes you can both buy and sell. `snapshot` appends the current totals to the store so `history` can show how the portfolio moved over time, and the HTML dashboard draws that series as an inline sparkline.

`python -m asset_allocator ...` works the same as `allocate ...`.

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
