"""Tax-lot cost-basis tracking: realized gains by FIFO or average cost.

Given a chronological list of buy/sell transactions for one holding, match sells
against the lots they consume and report realized gain/loss plus the remaining
cost basis. Pure, deterministic, offline. Illustrative only — not tax advice; the
exact rules (wash sales, lot selection, locale) are your accountant's call.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

METHODS = ("fifo", "average")


@dataclass(frozen=True)
class Transaction:
    action: str  # "buy" or "sell"
    quantity: float
    price: float
    date: str = ""


@dataclass(frozen=True)
class RealizedSale:
    date: str
    quantity: float
    proceeds: float
    cost_basis: float
    gain: float


@dataclass
class TaxLotResult:
    method: str
    realized_gain: float = 0.0
    total_proceeds: float = 0.0
    total_cost_sold: float = 0.0
    remaining_quantity: float = 0.0
    remaining_cost_basis: float = 0.0
    sales: list[RealizedSale] = field(default_factory=list)

    @property
    def remaining_avg_cost(self) -> float:
        return (
            self.remaining_cost_basis / self.remaining_quantity if self.remaining_quantity else 0.0
        )


class OversellError(ValueError):
    """Raised when a sell exceeds the quantity currently held."""


def _validate(tx: Transaction) -> None:
    if tx.action not in ("buy", "sell"):
        raise ValueError(f"action must be buy|sell, got {tx.action!r}")
    if tx.quantity <= 0:
        raise ValueError("quantity must be positive")
    if tx.price < 0:
        raise ValueError("price must be non-negative")


def _fifo(transactions: list[Transaction]) -> TaxLotResult:
    result = TaxLotResult(method="fifo")
    lots: deque[list[float]] = deque()  # each lot: [quantity, unit_cost]
    for tx in transactions:
        _validate(tx)
        if tx.action == "buy":
            lots.append([tx.quantity, tx.price])
            continue
        remaining = tx.quantity
        cost = 0.0
        while remaining > 1e-12:
            if not lots:
                raise OversellError(f"sold {tx.quantity} but not enough lots held")
            lot = lots[0]
            take = min(remaining, lot[0])
            cost += take * lot[1]
            lot[0] -= take
            remaining -= take
            if lot[0] <= 1e-12:
                lots.popleft()
        proceeds = tx.quantity * tx.price
        result.sales.append(RealizedSale(tx.date, tx.quantity, proceeds, cost, proceeds - cost))
    _finalize(result, [(lot[0], lot[1]) for lot in lots])
    return result


def _average(transactions: list[Transaction]) -> TaxLotResult:
    result = TaxLotResult(method="average")
    qty = 0.0
    basis = 0.0
    for tx in transactions:
        _validate(tx)
        if tx.action == "buy":
            qty += tx.quantity
            basis += tx.quantity * tx.price
            continue
        if tx.quantity > qty + 1e-9:
            raise OversellError(f"sold {tx.quantity} but only {qty} held")
        avg = basis / qty if qty else 0.0
        cost = tx.quantity * avg
        proceeds = tx.quantity * tx.price
        qty -= tx.quantity
        basis -= cost
        result.sales.append(RealizedSale(tx.date, tx.quantity, proceeds, cost, proceeds - cost))
    _finalize(result, [(qty, basis / qty if qty else 0.0)] if qty > 1e-12 else [])
    return result


def _finalize(result: TaxLotResult, remaining: list[tuple[float, float]]) -> None:
    result.realized_gain = round(sum(s.gain for s in result.sales), 6)
    result.total_proceeds = round(sum(s.proceeds for s in result.sales), 6)
    result.total_cost_sold = round(sum(s.cost_basis for s in result.sales), 6)
    result.remaining_quantity = round(sum(q for q, _ in remaining), 8)
    result.remaining_cost_basis = round(sum(q * c for q, c in remaining), 6)


def compute_taxlots(transactions: list[Transaction], method: str = "fifo") -> TaxLotResult:
    """Compute realized gains and remaining basis under ``fifo`` or ``average``."""
    if method == "fifo":
        return _fifo(transactions)
    if method == "average":
        return _average(transactions)
    raise ValueError(f"method must be one of {METHODS}, got {method!r}")
