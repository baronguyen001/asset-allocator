from __future__ import annotations

from typing import Protocol


class PriceError(Exception):
    """Raised when a keyless price provider cannot return a usable spot price."""


class PriceProvider(Protocol):
    def spot(self, ticker: str) -> float:
        """Return the latest spot price in the provider's native currency."""
