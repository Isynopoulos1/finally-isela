# Market Price Simulator

## Purpose

The simulator generates realistic-looking stock prices in-process with no external dependencies. It is the default provider when `MASSIVE_API_KEY` is not set.

It implements the same `MarketDataProvider` interface as the Massive client (see `MARKET_INTERFACE.md`), so the rest of the backend is oblivious to which is active.

---

## Price Model: Geometric Brownian Motion

Prices evolve using **GBM** — the standard model from quantitative finance.  
Each tick:

```
S(t+dt) = S(t) * exp((μ - 0.5σ²)dt + σ√dt * Z)
```

where:
- `S(t)` — current price
- `μ` — drift (annual, e.g. `0.05` = 5% yearly upward bias)
- `σ` — volatility (annual, e.g. `0.30` = 30% annualized)
- `dt` — time step in years (`0.5 / 252 / 6.5 / 3600` for a 0.5 s tick during a 6.5-hour trading day)
- `Z` — standard normal random variable

The exponential ensures prices can never go negative, and proportional moves look realistic.

---

## Correlated Moves

Tickers in the same sector move together via a **factor model**:

```
Z_i = ρ * Z_market + √(1 - ρ²) * Z_idiosyncratic
```

- `Z_market` — one shared normal draw per tick (represents "the market")
- `Z_idiosyncratic` — independent noise for each ticker
- `ρ` (correlation) — configurable per sector; default `0.6` for equities

This produces correlated sector moves without a full covariance matrix.

---

## Seed Prices

Realistic starting prices so the UI looks plausible from frame one:

```python
SEED_PRICES: dict[str, float] = {
    "AAPL":  190.00,
    "GOOGL": 175.00,
    "MSFT":  415.00,
    "AMZN":  185.00,
    "TSLA":  250.00,
    "NVDA":  875.00,
    "META":  490.00,
    "JPM":   200.00,
    "V":     275.00,
    "NFLX":  640.00,
}
DEFAULT_SEED_PRICE = 100.00  # fallback for unknown tickers
```

---

## Random Events

Every tick there is a small probability of a **price event** — a sudden 2–5% move to add drama:

```python
EVENT_PROB = 0.002      # ~0.2% per tick per ticker (~1 event/ticker/minute at 0.5s ticks)
EVENT_MAGNITUDE = (0.02, 0.05)  # 2% to 5% absolute move, direction random
```

Events are implemented as a one-tick multiplicative shock applied before the GBM step.

---

## Full Implementation

```python
# backend/market/simulator.py
import asyncio
import math
import random
import time
from backend.market.interface import MarketDataProvider, PriceUpdate

SEED_PRICES: dict[str, float] = {
    "AAPL": 190.00, "GOOGL": 175.00, "MSFT": 415.00, "AMZN": 185.00,
    "TSLA": 250.00, "NVDA": 875.00, "META": 490.00, "JPM": 200.00,
    "V": 275.00, "NFLX": 640.00,
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


def _gbm_step(price: float, market_z: float) -> float:
    idio_z = random.gauss(0, 1)
    z = MARKET_CORRELATION * market_z + math.sqrt(1 - MARKET_CORRELATION**2) * idio_z
    drift = (ANNUAL_DRIFT - 0.5 * ANNUAL_VOL**2) * DT
    diffusion = ANNUAL_VOL * math.sqrt(DT) * z
    return price * math.exp(drift + diffusion)


def _maybe_event(price: float) -> float:
    if random.random() < EVENT_PROB:
        magnitude = random.uniform(EVENT_MIN, EVENT_MAX)
        direction = random.choice([-1, 1])
        return price * (1 + direction * magnitude)
    return price


class SimulatorProvider(MarketDataProvider):
    def __init__(self) -> None:
        self._prices: dict[str, float] = {}
        self._cache: dict[str, PriceUpdate] = {}
        self._task: asyncio.Task | None = None

    async def start(self, tickers: list[str]) -> None:
        for t in tickers:
            self._prices[t] = SEED_PRICES.get(t, DEFAULT_SEED)
        self._task = asyncio.create_task(self._tick_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    def get_prices(self) -> dict[str, PriceUpdate]:
        return dict(self._cache)

    async def update_tickers(self, tickers: list[str]) -> None:
        for t in tickers:
            if t not in self._prices:
                self._prices[t] = SEED_PRICES.get(t, DEFAULT_SEED)
        # Remove tickers no longer watched
        for t in list(self._prices):
            if t not in tickers:
                del self._prices[t]
                self._cache.pop(t, None)

    async def _tick_loop(self) -> None:
        while True:
            try:
                self._tick()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(TICK_SECONDS)

    def _tick(self) -> None:
        now = time.time()
        market_z = random.gauss(0, 1)
        for ticker, price in list(self._prices.items()):
            new_price = _gbm_step(_maybe_event(price), market_z)
            new_price = max(new_price, 0.01)  # floor at $0.01

            old = self._cache.get(ticker)
            prev_price = old.price if old else price
            prev_close = SEED_PRICES.get(ticker, DEFAULT_SEED)
            change_pct = (new_price - prev_close) / prev_close * 100

            self._prices[ticker] = new_price
            self._cache[ticker] = PriceUpdate(
                ticker=ticker,
                price=round(new_price, 2),
                prev_price=round(prev_price, 2),
                change_pct=round(change_pct, 3),
                timestamp=now,
            )
```

---

## Parameters Summary

| Constant | Value | Meaning |
|----------|-------|---------|
| `ANNUAL_DRIFT` | `0.05` | 5% yearly upward drift |
| `ANNUAL_VOL` | `0.30` | 30% annualized volatility |
| `MARKET_CORRELATION` | `0.60` | Cross-ticker correlation |
| `TICK_SECONDS` | `0.5` | Update interval |
| `EVENT_PROB` | `0.002` | Per-tick probability of a surprise move |
| `EVENT_MIN/MAX` | `0.02–0.05` | Surprise move magnitude (2%–5%) |

---

## Behavior Characteristics

- **Tick rate**: 0.5 s → 2 updates/second/ticker
- **Typical daily range**: ±1–3% (consistent with `σ = 0.30` annualized)
- **Correlated sector moves**: tech stocks visibly move together during large market_z draws
- **Price events**: roughly 1 surprise move per ticker per 8 minutes of runtime
- **Memory**: O(n tickers) — negligible
- **CPU**: One goroutine-equivalent (`asyncio.Task`) doing light float arithmetic — effectively zero overhead

---

## Notes

- The simulator uses `random` (not `numpy`) to avoid an extra dependency. Precision is sufficient for a demo.
- `prev_close` is pinned to the seed price rather than a true EOD value. This means `change_pct` drifts from reality over time — intentional; it makes the demo P&L chart more interesting.
- Extending to numpy-based vectorized updates is straightforward if performance ever matters with hundreds of tickers.
