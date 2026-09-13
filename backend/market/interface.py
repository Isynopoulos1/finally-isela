"""Provider contract shared by the simulator and the Massive client.

Downstream code (SSE streaming, price cache, portfolio valuation) depends
only on this module — it never needs to know which provider is active.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceUpdate:
    """One price observation for one ticker."""

    ticker: str
    price: float
    prev_price: float  # price at the previous observation (drives the flash)
    change_pct: float  # % change from the previous close
    timestamp: float  # Unix seconds


class MarketDataProvider(ABC):
    """Source of live prices. Owns a background task and an in-memory cache."""

    name: str  # "simulator" | "massive" — reported by /api/health

    @abstractmethod
    async def start(self, tickers: list[str]) -> None:
        """Seed the cache and launch the background task. Called once at startup."""

    @abstractmethod
    async def stop(self) -> None:
        """Cancel the background task and wait for it to finish."""

    @abstractmethod
    def get_prices(self) -> dict[str, PriceUpdate]:
        """Latest update per tracked ticker. Synchronous cache read; may be empty."""

    @abstractmethod
    async def update_tickers(self, tickers: list[str]) -> None:
        """Replace the tracked ticker set (watchlist or positions changed)."""
