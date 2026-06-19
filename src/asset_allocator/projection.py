"""Illustrative compound-growth projection for contribution planning.

NOT FINANCIAL ADVICE. A projection is deterministic arithmetic on USER-SUPPLIED
assumptions (a single fixed assumed return and a fixed contribution). Real markets are
not fixed-rate, so this is a planning illustration only, not a forecast, a guarantee, or
a recommendation.
"""

from __future__ import annotations

from asset_allocator.models import ProjectionRow


def project(
    initial: float,
    monthly: float,
    annual_return_pct: float,
    years: int,
    *,
    inflation_pct: float = 0.0,
) -> list[ProjectionRow]:
    """Project a balance forward year by year with monthly contributions.

    Contributions compound monthly at the monthly-equivalent of the assumed annual rate.
    `real` discounts the nominal balance by the assumed annual inflation; `growth` is the
    nominal balance minus everything contributed (initial + all monthly deposits) so far.
    """
    if years < 1:
        raise ValueError("years must be at least 1.")
    if monthly < 0:
        raise ValueError("monthly contribution must be non-negative.")
    monthly_rate = (1.0 + annual_return_pct / 100.0) ** (1.0 / 12.0) - 1.0
    balance = float(initial)
    contributed = float(initial)
    rows: list[ProjectionRow] = []
    for year in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1.0 + monthly_rate) + monthly
            contributed += monthly
        real = balance / ((1.0 + inflation_pct / 100.0) ** year)
        rows.append(
            ProjectionRow(
                year=year,
                contributed=round(contributed, 2),
                nominal=round(balance, 2),
                real=round(real, 2),
                growth=round(balance - contributed, 2),
            )
        )
    return rows
