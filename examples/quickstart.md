# Quickstart

This walkthrough uses fictional demo data and cached demo prices, so it works without network access or API keys.

```bash
allocate init --from-file examples/sample_answers.json
allocate plan --amount 100000
allocate add --bucket equity --label "Demo Equity Fund" --kind market --ticker demo.us --quantity 10 --cost 3000
allocate status --no-refresh --store examples/sample_portfolio.json
allocate report --html dashboard.html --no-refresh --store examples/sample_portfolio.json
```

The output is for planning practice only. NOT FINANCIAL ADVICE.
