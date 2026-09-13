"""In-process market data simulator — the default provider.

Prices evolve via geometric Brownian motion (GBM) with a shared per-tick
market factor so tickers move together, plus occasional random "events" for
drama. No external dependencies; runs as a single background asyncio task.
"""

import asyncio
import logging
import math
import random
import time
from contextlib import suppress

from market.interface import MarketDataProvider, PriceUpdate

log = logging.getLogger(__name__)

SEED_PRICES: dict[str, float] = {
    "AAPL": 190.00,
    "GOOGL": 175.00,
    "MSFT": 415.00,
    "AMZN": 185.00,
    "TSLA": 250.00,
    "NVDA": 875.00,
    "META": 490.00,
    "JPM": 200.00,
    "V": 275.00,
    "NFLX": 640.00,
}
DEFAULT_SEED = 100.00

ANNUAL_DRIFT = 0.05
ANNUAL_VOL = 0.30
MARKET_CORRELATION = 0.60
TICK_SECONDS = 0.5
TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600
DT = TICK_SECONDS / TRADING_SECONDS_PER_YEAR

EVENT_PROB = 0.002
EVENT_MIN = 0.02
EVENT_MAX = 0.05

MIN_PRICE = 0.01


def gbm_step(price: float, market_z: float) -> float:
    """Advance one price by a single GBM tick, correlated with the market draw.

    `market_z` is the one shared normal draw per tick; each ticker correlates
    with it at MARKET_CORRELATION, which makes any two tickers correlate with
    each other at MARKET_CORRELATION**2.
    """
    idio_z = random.gauss(0, 1)
    z = MARKET_CORRELATION * market_z + math.sqrt(1 - MARKET_CORRELATION**2) * idio_z
    drift = (ANNUAL_DRIFT - 0.5 * ANNUAL_VOL**2) * DT
    diffusion = ANNUAL_VOL * math.sqrt(DT) * z
    return price * math.exp(drift + diffusion)


def maybe_event(price: float) -> float:
    """Occasionally apply a 2-5% shock, direction random."""
    if random.random() >= EVENT_PROB:
        return price
    magnitude = random.uniform(EVENT_MIN, EVENT_MAX)
    return price * (1 + random.choice([-1, 1]) * magnitude)


class SimulatorProvider(MarketDataProvider):
    """In-process GBM price generator. No external dependencies."""

    name = "simulator"

    def __init__(self) -> None:
        self._prices: dict[str, float] = {}  # full-precision working prices
        self._closes: dict[str, float] = {}  # pinned "previous close" per ticker
        self._cache: dict[str, PriceUpdate] = {}
        self._task: asyncio.Task | None = None

    async def start(self, tickers: list[str]) -> None:
        self._seed(tickers)
        self._tick()  # populate the cache before the first client connects
        self._task = asyncio.create_task(self._tick_loop(), name="simulator-tick")
        log.info("Simulator started with %d tickers", len(self._prices))

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    def get_prices(self) -> dict[str, PriceUpdate]:
        return dict(self._cache)

    async def update_tickers(self, tickers: list[str]) -> None:
        new_tickers = [t for t in tickers if t not in self._prices]
        self._seed(tickers)
        for ticker in set(self._prices) - set(tickers):
            del self._prices[ticker]
            del self._closes[ticker]
            self._cache.pop(ticker, None)
        # Populate cache immediately for new tickers so get_prices() reflects them
        # before the next background tick fires.
        if new_tickers:
            now = time.time()
            market_z = random.gauss(0, 1)
            for ticker in new_tickers:
                price = self._prices[ticker]
                new_price = max(gbm_step(maybe_event(price), market_z), MIN_PRICE)
                self._prices[ticker] = new_price
                self._cache[ticker] = PriceUpdate(
                    ticker=ticker,
                    price=round(new_price, 2),
                    prev_price=round(price, 2),
                    change_pct=round((new_price - self._closes[ticker]) / self._closes[ticker] * 100, 3),
                    timestamp=now,
                )

    def _seed(self, tickers: list[str]) -> None:
        """Give any unknown ticker a realistic starting price and previous close."""
        for ticker in tickers:
            if ticker not in self._prices:
                seed = SEED_PRICES.get(ticker, DEFAULT_SEED)
                self._prices[ticker] = seed
                self._closes[ticker] = seed

    async def _tick_loop(self) -> None:
        while True:
            await asyncio.sleep(TICK_SECONDS)
            self._tick()

    def _tick(self) -> None:
        """Advance every tracked price once. Pure arithmetic — no awaits, no I/O."""
        now = time.time()
        market_z = random.gauss(0, 1)
        for ticker, price in list(self._prices.items()):
            new_price = max(gbm_step(maybe_event(price), market_z), MIN_PRICE)
            self._prices[ticker] = new_price

            cached = self._cache.get(ticker)
            prev_price = cached.price if cached else round(price, 2)
            close = self._closes[ticker]
            self._cache[ticker] = PriceUpdate(
                ticker=ticker,
                price=round(new_price, 2),
                prev_price=prev_price,
                change_pct=round((new_price - close) / close * 100, 3),
                timestamp=now,
            )
