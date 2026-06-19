# Quickstart

This walkthrough uses fictional demo data and cached demo prices, so it works without network access or API keys.

```bash
allocate init --from-file examples/sample_answers.json
allocate plan --amount 100000
allocate add --bucket equity --label "Demo Equity Fund" --kind market --ticker demo.us --quantity 10 --cost 3000
allocate status --no-refresh --store examples/sample_portfolio.json

# Bulk-load holdings from a spreadsheet (inverse of `export`):
allocate import --csv examples/sample_holdings.csv --replace --store /tmp/imported.json

# Set your own target weights instead of a model template (re-normalized to 100%):
allocate set-target --weight equity=60 --weight bonds=25 --weight gold=15 --store examples/sample_portfolio.json

# Plan a fresh deposit buy-only (no selling), toward the target weights:
allocate contribute --amount 5000 --no-refresh --store examples/sample_portfolio.json

# Project compound growth from monthly contributions (illustrative, not a forecast):
allocate project --years 20 --monthly 500 --annual-return 7 --inflation 3

# Record a snapshot now, then review the value series over time:
allocate snapshot --note "monthly check-in" --no-refresh --store examples/sample_portfolio.json
allocate history --store examples/sample_portfolio.json

# Export the current status for a spreadsheet, and render the dashboard:
allocate export --format csv --out status.csv --no-refresh --store examples/sample_portfolio.json
allocate report --html dashboard.html --no-refresh --store examples/sample_portfolio.json
```

The output is for planning practice only. NOT FINANCIAL ADVICE.
