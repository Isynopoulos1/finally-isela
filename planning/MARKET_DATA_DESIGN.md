# Market Data — Detailed Backend Design

Implementation-level design for the FinAlly market data subsystem. This document
consolidates and supersedes the sketches in `MARKET_INTERFACE.md`,
`MARKET_SIMULATOR.md` and `MASSIVE_API.md` — those remain the reference for the
Massive REST payload shapes and the GBM rationale; this document is what the
Backend agent implements.

---

## 1. Scope

Everything from "a price is produced" to "a price reaches the browser":

- The provider contract shared by simulator and Massive client
- The GBM simulator (default)
- The Massive REST poller (optional, key-driven)
- The rolling price history used by the main chart
- The SSE endpoint and its delta protocol
- App wiring, watchlist propagation, health reporting
- Unit tests

Out of scope: portfolio valuation and trade execution (they consume
`get_prices()` and nothing more).

---

## 2. Decisions — resolving the open questions

`PLAN.md` §13 raises several questions about market data. Resolutions:

| Question | Resolution |
|---|---|
| Is the SSE stream scoped to the watchlist or a wider universe? | **Tracked tickers = watchlist ∪ tickers with an open position.** A user can sell a stock out of the watchlist while still holding it; portfolio valuation needs that price. One set, computed in one place (§8.2). |
| Where does the main chart get history? | **A rolling in-memory buffer** sampled from the provider cache every 2 s, exposed at `GET /api/prices/{ticker}/history`. 30-minute window, no database writes. Resets on container restart — acceptable and documented. |
| Do sparklines reset on refresh? | Yes, they accumulate from SSE. The frontend *may* prime them from the history endpoint for a better first paint; both work. |
| Build the abstraction up front, or simulator-first? | **Build the abstraction — it is 30 lines.** The two implementations already exist in sketch form; collapsing them would cost more later than it saves now. |
| Keep `PriceUpdate` as specified? | **Yes, unchanged.** It is the published contract other agents code against. The only addition to the interface is a `name` class attribute for health reporting (§3). |

---

## 3. The contract

```python
# backend/market/interface.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceUpdate:
    """One price observation for one ticker."""

    ticker: str
    price: float
    prev_price: float      # price at the previous observation (drives the flash)
    change_pct: float      # % change from the previous close
    timestamp: float       # Unix seconds


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
```

### Contract rules

1. **`get_prices()` never blocks and never raises.** It returns a shallow copy so
   callers can iterate while the background task mutates the cache.
2. **`timestamp` is the change signal.** A ticker's timestamp advances only when
   a new observation arrives. The SSE layer diffs on it (§7), so a 15-second
   Massive poll does not produce 30 redundant pushes.
3. **`prev_price` is the previous *observation*, not the previous close.** Equal
   to `price` when nothing moved — the frontend then draws no flash.
4. **`update_tickers` both adds and prunes.** Tickers dropped from the set are
   removed from the cache so stale prices cannot leak into valuations.

### Ticker normalisation

Everything upstream (DB, chat, API routes) must hand providers uppercase,
whitespace-stripped symbols. One helper, used at every entry point:

```python
# backend/market/tickers.py
def normalize(raw: str) -> str:
    """'  aapl ' -> 'AAPL'."""
    return raw.strip().upper()


def normalize_all(raw: list[str]) -> list[str]:
    """Normalise, drop blanks, de-duplicate, preserve order."""
    seen: dict[str, None] = {}
    for item in raw:
        ticker = normalize(item)
        if ticker:
            seen[ticker] = None
    return list(seen)
```

---

## 4. Simulator (default provider)

### 4.1 Model

Geometric Brownian motion, one step per tick:

```
S(t+dt) = S(t) · exp((μ − ½σ²)·dt + σ·√dt·Z)
Z_i     = ρ·Z_market + √(1 − ρ²)·Z_i,idiosyncratic
```

The single shared `Z_market` draw per tick makes every ticker move together —
the whole board goes green or red at once, which reads as "the market" without a
covariance matrix. The exponential keeps prices positive.

**`ρ` is the market factor loading, not the pairwise correlation.** Each ticker
correlates with the market factor at `ρ`, but two tickers correlate with *each
other* at `ρ²`. At `ρ = 0.60` that is **0.36 between any two tickers** —
verified numerically, and a realistic figure for large-cap equities.
`MARKET_SIMULATOR.md` labels this constant "cross-ticker correlation", which is
off by a square; the code is right and the label is wrong. To target a pairwise
correlation `c`, set `MARKET_CORRELATION = √c`.

### 4.2 Implementation

```python
# backend/market/simulator.py
import asyncio
import logging
import math
import random
import time
from contextlib import suppress

from backend.market.interface import MarketDataProvider, PriceUpdate

log = logging.getLogger(__name__)

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

MIN_PRICE = 0.01


def gbm_step(price: float, market_z: float) -> float:
    """Advance one price by a single GBM tick, correlated with the market draw."""
    idio_z = random.gauss(0, 1)
    z = MARKET_CORRELATION * market_z + math.sqrt(1 - MARKET_CORRELATION**2) * idio_z
    drift = (ANNUAL_DRIFT - 0.5 * ANNUAL_VOL**2) * DT
    diffusion = ANNUAL_VOL * math.sqrt(DT) * z
    return price * math.exp(drift + diffusion)


def maybe_event(price: float) -> float:
    """Occasionally apply a 2–5% shock, direction random."""
    if random.random() >= EVENT_PROB:
        return price
    magnitude = random.uniform(EVENT_MIN, EVENT_MAX)
    return price * (1 + random.choice([-1, 1]) * magnitude)


class SimulatorProvider(MarketDataProvider):
    """In-process GBM price generator. No external dependencies."""

    name = "simulator"

    def __init__(self) -> None:
        self._prices: dict[str, float] = {}   # full-precision working prices
        self._closes: dict[str, float] = {}   # pinned "previous close" per ticker
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
        self._seed(tickers)
        for ticker in set(self._prices) - set(tickers):
            del self._prices[ticker]
            del self._closes[ticker]
            self._cache.pop(ticker, None)

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
```

### 4.3 Notes on the implementation

- **`_tick` holds no awaits.** It runs to completion between event-loop turns, so
  `get_prices()` can never observe a half-written cache. This is the entire
  concurrency story (§9) — no locks.
- **Cancellation is not caught.** `CancelledError` propagates out of
  `asyncio.sleep`, ends the task, and `stop()` awaits it. Swallowing it would
  make shutdown hang.
- **No `try/except` around `_tick`.** It is float arithmetic over a dict; there
  is nothing to recover from. A crash here is a bug we want to see.
- **Sleep-then-tick.** `start()` produces the first tick synchronously, so the
  cache is warm the instant the app accepts requests.
- **`_closes` is pinned at seed time**, so `change_pct` is "% since this ticker
  started being tracked". Deliberate: it drifts away from a real daily change but
  keeps the board colourful. Tickers added mid-session start at 0.00%.

### 4.4 Tuning — what these numbers actually look like

Per-tick standard deviation is `σ·√dt = 0.30 · √(8.48e-8) ≈ 8.7e-5`, i.e. **0.0087%
per tick**:

| Horizon | Ticks | ≈ 1σ move |
|---|---|---|
| 1 tick | 1 | 0.009% |
| 1 minute | 120 | 0.10% |
| 5 minutes | 600 | 0.21% |
| Full 6.5 h day | 46 800 | 1.9% |

So in a five-minute demo, **GBM diffusion is nearly invisible; the random events
are what the user sees**. At `EVENT_PROB = 0.002` and 2 ticks/second that is
`0.002 × 600 ≈ 1.2` events per ticker per five minutes — with ten tickers, an
event somewhere on the board every ~25 seconds. That is the intended balance: a
calm tape punctuated by drama.

One consequence worth knowing before picking seed prices: prices are rounded to
cents, so a ticker only visibly flashes when its typical tick move exceeds
$0.005 — i.e. **above $57**. All ten default tickers clear this comfortably. A
ticker added at `DEFAULT_SEED = 100.00` is fine, but a genuinely low-priced one
would sit visibly frozen between events. Raise `ANNUAL_VOL` if that ever
matters; do not add knobs before it does.

---

## 5. Massive provider (optional)

Selected when `MASSIVE_API_KEY` is non-empty. Polls the multi-ticker snapshot
endpoint — one HTTP call covers the whole tracked set, which keeps the free tier
(5 req/min) comfortable at a 15-second interval.

See `MASSIVE_API.md` for the full response shape.

```python
# backend/market/massive.py
import asyncio
import logging
import os
import time
from contextlib import suppress

import httpx

from backend.market.interface import MarketDataProvider, PriceUpdate

log = logging.getLogger(__name__)

BASE_URL = "https://api.massive.com"
SNAPSHOT_PATH = "/v2/snapshot/locale/us/markets/stocks/tickers"
REQUEST_TIMEOUT = 10.0
RATE_LIMIT_BACKOFF = 60.0
DEFAULT_POLL_INTERVAL = 15.0


def poll_interval() -> float:
    return float(os.getenv("MASSIVE_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL))


class MassiveProvider(MarketDataProvider):
    """Polls the Massive REST snapshot endpoint into the shared price cache."""

    name = "massive"

    def __init__(self, api_key: str, interval: float | None = None) -> None:
        self._api_key = api_key
        self._interval = interval if interval is not None else poll_interval()
        self._tickers: list[str] = []
        self._cache: dict[str, PriceUpdate] = {}
        self._task: asyncio.Task | None = None
        self._disabled = False

    async def start(self, tickers: list[str]) -> None:
        self._tickers = tickers
        self._task = asyncio.create_task(self._poll_loop(), name="massive-poll")
        log.info("Massive provider started, polling every %.0fs", self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    def get_prices(self) -> dict[str, PriceUpdate]:
        return dict(self._cache)

    async def update_tickers(self, tickers: list[str]) -> None:
        self._tickers = tickers
        for ticker in set(self._cache) - set(tickers):
            del self._cache[ticker]

    async def _poll_loop(self) -> None:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=REQUEST_TIMEOUT) as client:
            while True:
                delay = await self._poll_once(client)
                if delay is None:
                    self._disabled = True
                    return
                await asyncio.sleep(delay)

    async def _poll_once(self, client: httpx.AsyncClient) -> float | None:
        """One snapshot fetch. Returns seconds until the next poll, or None to stop."""
        if not self._tickers:
            return self._interval

        params = {"tickers": ",".join(self._tickers), "apiKey": self._api_key}
        try:
            resp = await client.get(SNAPSHOT_PATH, params=params)
        except httpx.HTTPError as exc:
            log.warning("Massive request failed: %s", exc)
            return self._interval

        if resp.status_code == 429:
            log.warning("Massive rate limit hit — backing off %.0fs", RATE_LIMIT_BACKOFF)
            return RATE_LIMIT_BACKOFF
        if resp.status_code in (401, 403):
            log.error("Massive rejected the API key (%d) — polling disabled. "
                      "Unset MASSIVE_API_KEY to use the simulator.", resp.status_code)
            return None
        if resp.status_code >= 400:
            log.error("Massive returned %d: %s", resp.status_code, resp.text[:200])
            return self._interval

        self._apply(resp.json())
        return self._interval

    def _apply(self, payload: dict) -> None:
        tracked = set(self._tickers)
        for snapshot in payload.get("tickers", []):
            update = self._parse(snapshot, self._cache.get(snapshot.get("ticker", "")))
            if update and update.ticker in tracked:
                self._cache[update.ticker] = update

    @staticmethod
    def _parse(snapshot: dict, cached: PriceUpdate | None) -> PriceUpdate | None:
        """Map one snapshot entry onto PriceUpdate. None if it carries no price."""
        ticker = snapshot.get("ticker")
        prev_day = snapshot.get("prevDay") or {}
        last_trade = snapshot.get("lastTrade") or {}
        prev_close = prev_day.get("c")
        price = last_trade.get("p") or prev_close  # pre-market: fall back to close
        if not ticker or not price:
            return None

        updated_ns = snapshot.get("updated")
        return PriceUpdate(
            ticker=ticker,
            price=round(price, 2),
            prev_price=cached.price if cached else round(prev_close or price, 2),
            change_pct=round(snapshot.get("todaysChangePerc", 0.0), 3),
            timestamp=updated_ns / 1e9 if updated_ns else time.time(),
        )
```

### 5.1 Notes

- **`timestamp` comes from the exchange (`updated`, nanoseconds), not the wall
  clock.** When a ticker has not traded between polls its timestamp is unchanged,
  the SSE diff skips it, and the browser stays quiet. Using `time.time()` here
  would push identical prices every 15 s and defeat the diff.
- **`_parse` is a pure static function** so the parsing tests need no network, no
  event loop and no provider instance (§10.2).
- **Pre-market / halted tickers**: `lastTrade.p` may be absent; we fall back to
  `prevDay.c`. If neither exists the entry is skipped rather than cached as zero.
- **Bad key is fatal-but-quiet.** The loop exits, `/api/health` reports
  `"provider": "massive", "healthy": false`, and the UI shows no prices. We do
  *not* silently fall back to the simulator: showing fake prices to someone who
  asked for real ones is worse than showing none.
- **429 backs off once** and returns to the normal cadence. If it recurs, raise
  `MASSIVE_POLL_INTERVAL_SECONDS`.

---

## 6. Factory and configuration

```python
# backend/market/factory.py
import logging
import os

from backend.market.interface import MarketDataProvider
from backend.market.massive import MassiveProvider
from backend.market.simulator import SimulatorProvider

log = logging.getLogger(__name__)


def make_provider() -> MarketDataProvider:
    """Massive when a key is configured, simulator otherwise."""
    api_key = os.getenv("MASSIVE_API_KEY", "").strip()
    if api_key:
        log.info("MASSIVE_API_KEY present — using live market data")
        return MassiveProvider(api_key)
    log.info("No MASSIVE_API_KEY — using the price simulator")
    return SimulatorProvider()
```

| Variable | Default | Effect |
|---|---|---|
| `MASSIVE_API_KEY` | *(empty)* | Non-empty selects the Massive provider |
| `MASSIVE_POLL_INTERVAL_SECONDS` | `15` | Poll cadence; safe for the 5 req/min free tier |

Simulator parameters stay module constants — they are tuning, not deployment
configuration.

---

## 7. Price history

Sampling the provider cache from a small recorder task gives the main chart real
data without touching either provider, and without a database write path.

```python
# backend/market/history.py
import asyncio
from collections import deque

from backend.market.interface import MarketDataProvider, PriceUpdate

SAMPLE_SECONDS = 2.0
MAX_POINTS = 900  # 30 minutes at one sample per 2 s


class PriceHistory:
    """Rolling per-ticker price series, sampled from the provider cache."""

    def __init__(self, max_points: int = MAX_POINTS) -> None:
        self._series: dict[str, deque[tuple[float, float]]] = {}
        self._max_points = max_points

    def record(self, prices: dict[str, PriceUpdate]) -> None:
        for ticker, update in prices.items():
            series = self._series.get(ticker)
            if series is None:
                series = self._series[ticker] = deque(maxlen=self._max_points)
            if not series or series[-1][0] != update.timestamp:
                series.append((update.timestamp, update.price))
        for ticker in set(self._series) - set(prices):
            del self._series[ticker]

    def get(self, ticker: str) -> list[dict[str, float]]:
        return [{"t": t, "p": p} for t, p in self._series.get(ticker, ())]


async def record_loop(provider: MarketDataProvider, history: PriceHistory) -> None:
    while True:
        await asyncio.sleep(SAMPLE_SECONDS)
        history.record(provider.get_prices())
```

```python
# backend/routes/prices.py
from fastapi import APIRouter, Request

from backend.market.tickers import normalize

router = APIRouter(prefix="/api/prices")


@router.get("/{ticker}/history")
async def price_history(ticker: str, request: Request) -> dict:
    """Recent price points for the main chart. Empty list for untracked tickers."""
    symbol = normalize(ticker)
    return {"ticker": symbol, "points": request.app.state.history.get(symbol)}
```

Bounded by construction: `MAX_POINTS` × tracked tickers × 2 floats ≈ 20 tickers →
36 000 points → well under a megabyte.

---

## 8. Wiring

### 8.1 SSE endpoint

The stream sends a **full snapshot on connect, then only what changed**. With the
simulator that is every ticker every 500 ms; with Massive it is a handful of
tickers every 15 s instead of the whole board 30 times over.

```python
# backend/routes/stream.py
import asyncio
import json
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.market.interface import PriceUpdate

router = APIRouter(prefix="/api/stream")

PUSH_INTERVAL = 0.5
HEARTBEAT_SECONDS = 15.0
RETRY_MS = 3000

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # stops proxies buffering the stream
}


def _payload(update: PriceUpdate) -> dict:
    return {
        "price": update.price,
        "prev_price": update.prev_price,
        "change_pct": update.change_pct,
        "timestamp": update.timestamp,
    }


@router.get("/prices")
async def price_stream(request: Request) -> StreamingResponse:
    provider = request.app.state.market

    async def events():
        yield f"retry: {RETRY_MS}\n\n"
        sent: dict[str, float] = {}  # ticker -> timestamp last pushed
        last_send = time.monotonic()

        while not await request.is_disconnected():
            prices = provider.get_prices()
            changed = {t: u for t, u in prices.items() if sent.get(t) != u.timestamp}
            sent = {t: u.timestamp for t, u in prices.items()}

            if changed:
                body = json.dumps({t: _payload(u) for t, u in changed.items()})
                yield f"event: prices\ndata: {body}\n\n"
                last_send = time.monotonic()
            elif time.monotonic() - last_send > HEARTBEAT_SECONDS:
                yield ": keep-alive\n\n"
                last_send = time.monotonic()

            await asyncio.sleep(PUSH_INTERVAL)

    return StreamingResponse(events(), media_type="text/event-stream", headers=SSE_HEADERS)
```

`sent` is rebuilt from `prices` on **every** round, not only when something
changed. That detail matters: it is what drops tickers which left the tracked
set. Doing it inside the `if changed:` branch leaves a removed ticker's stale
timestamp in `sent` indefinitely, and a later re-add carrying that same
timestamp — possible with Massive, where the timestamp comes from the exchange —
would be diffed away and never sent, leaving a permanently blank row.

The stream never announces removals — the frontend renders rows from
`GET /api/watchlist` and looks prices up by ticker, so a vanished ticker simply
stops updating and disappears with the next watchlist fetch.

Client side:

```ts
const source = new EventSource("/api/stream/prices");
source.addEventListener("prices", (e) => {
  const updates: Record<string, Quote> = JSON.parse(e.data);
  // merge into state; flash where price !== prev_price
});
source.onerror = () => setStatus("reconnecting"); // EventSource retries on its own
```

### 8.2 Tracked tickers and lifespan

```python
# backend/market/tracking.py
from fastapi import FastAPI

from backend.db import get_position_tickers, get_watchlist_tickers
from backend.market.tickers import normalize_all


async def tracked_tickers() -> list[str]:
    """Everything needing a live price: watchlist plus anything we still hold."""
    return normalize_all(await get_watchlist_tickers() + await get_position_tickers())


async def refresh_tracked(app: FastAPI) -> None:
    """Re-sync the provider after a watchlist change or a trade."""
    await app.state.market.update_tickers(await tracked_tickers())
```

```python
# backend/main.py
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from backend.market.factory import make_provider
from backend.market.history import PriceHistory, record_loop
from backend.market.tracking import tracked_tickers


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.market = make_provider()
    app.state.history = PriceHistory()
    await app.state.market.start(await tracked_tickers())
    recorder = asyncio.create_task(
        record_loop(app.state.market, app.state.history), name="history-recorder"
    )
    yield
    recorder.cancel()
    with suppress(asyncio.CancelledError):
        await recorder
    await app.state.market.stop()


app = FastAPI(lifespan=lifespan)
```

Call `refresh_tracked(request.app)` after every mutation that can change the set:
`POST /api/watchlist`, `DELETE /api/watchlist/{ticker}`, `POST /api/portfolio/trade`,
and the chat route's auto-executed actions.

### 8.3 Health

```python
@router.get("/api/health")
async def health(request: Request) -> dict:
    prices = request.app.state.market.get_prices()
    return {
        "status": "ok",
        "provider": request.app.state.market.name,
        "tickers": len(prices),
        "healthy": bool(prices),
    }
```

`healthy: false` with `provider: "massive"` is the visible symptom of a rejected
API key.

---

## 9. Concurrency

Everything runs on one event loop in one process:

- Providers mutate their cache inside a synchronous method with no `await`, so a
  tick or a snapshot application is atomic with respect to every reader. No locks.
- `get_prices()` returns a shallow copy; `PriceUpdate` is frozen. Readers cannot
  corrupt provider state and cannot see a partial update.
- Each SSE client owns its own generator and `sent` dict. N clients cost N
  timers, not N price streams — the single background task is the only producer.
- Shutdown order is recorder → provider, both cancelled and awaited, so no task
  outlives the app.

---

## 10. Tests

`backend/tests/test_market_*.py`, pytest with `pytest-asyncio`.

### 10.1 Simulator

```python
import statistics

import pytest

from backend.market.simulator import (
    ANNUAL_VOL, DT, MARKET_CORRELATION, SEED_PRICES, SimulatorProvider, gbm_step,
)


def _correlation(x: list[float], y: list[float]) -> float:
    mx, my = statistics.mean(x), statistics.mean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x)
    return cov / (statistics.pstdev(x) * statistics.pstdev(y))


def test_gbm_keeps_prices_positive():
    price = 100.0
    for _ in range(10_000):
        price = gbm_step(price, market_z=-4.0)  # sustained crash
    assert price > 0


def test_gbm_step_distribution():
    """Per-tick log return matches sigma*sqrt(dt) when the market draw is random.

    market_z must be drawn per call: pinning it to 0.0 strips out the market
    factor and damps the observed sd by sqrt(1 - rho**2) = 0.8.
    """
    import math, random, statistics
    returns = [
        math.log(gbm_step(100.0, random.gauss(0, 1)) / 100.0)
        for _ in range(50_000)
    ]
    expected_sd = ANNUAL_VOL * math.sqrt(DT)
    assert statistics.stdev(returns) == pytest.approx(expected_sd, rel=0.05)
    assert statistics.mean(returns) == pytest.approx(0.0, abs=expected_sd)


def test_tickers_are_correlated_at_rho_squared():
    """Two tickers sharing a market draw correlate at rho**2, not rho."""
    import math, random
    market = [random.gauss(0, 1) for _ in range(50_000)]
    a = [math.log(gbm_step(100.0, z) / 100.0) for z in market]
    b = [math.log(gbm_step(100.0, z) / 100.0) for z in market]
    assert _correlation(a, b) == pytest.approx(MARKET_CORRELATION**2, abs=0.03)


@pytest.mark.asyncio
async def test_start_populates_cache_immediately():
    provider = SimulatorProvider()
    await provider.start(["AAPL", "MSFT"])
    try:
        prices = provider.get_prices()
        assert set(prices) == {"AAPL", "MSFT"}
        assert prices["AAPL"].price == pytest.approx(SEED_PRICES["AAPL"], rel=0.01)
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_update_tickers_adds_and_prunes():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    try:
        await provider.update_tickers(["MSFT"])
        assert set(provider.get_prices()) == {"MSFT"}
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_stop_is_idempotent_and_cancels_the_task():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    await provider.stop()
    await provider.stop()
    assert provider._task.cancelled()
```

### 10.2 Massive parsing

`_parse` is static and pure, so parsing needs no network:

```python
from backend.market.massive import MassiveProvider, PriceUpdate

SNAPSHOT = {
    "ticker": "AAPL",
    "todaysChangePerc": 0.82,
    "updated": 1_720_000_000_000_000_000,
    "lastTrade": {"p": 190.05},
    "prevDay": {"c": 188.50},
}


def test_parse_maps_snapshot_fields():
    update = MassiveProvider._parse(SNAPSHOT, cached=None)
    assert update == PriceUpdate("AAPL", 190.05, 188.50, 0.82, 1_720_000_000.0)


def test_parse_uses_cached_price_as_prev_price():
    cached = PriceUpdate("AAPL", 189.00, 188.00, 0.3, 1.0)
    assert MassiveProvider._parse(SNAPSHOT, cached).prev_price == 189.00


def test_parse_falls_back_to_previous_close_pre_market():
    snapshot = SNAPSHOT | {"lastTrade": {}}
    assert MassiveProvider._parse(snapshot, None).price == 188.50


def test_parse_skips_entries_with_no_price():
    assert MassiveProvider._parse({"ticker": "AAPL"}, None) is None
```

Transport-level behaviour uses `httpx.MockTransport`:

```python
import httpx
import pytest

from backend.market.massive import MassiveProvider, RATE_LIMIT_BACKOFF


def client_returning(response: httpx.Response) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response))


@pytest.mark.asyncio
async def test_poll_once_caches_prices():
    body = {"tickers": [SNAPSHOT]}
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(200, json=body)) as client:
        assert await provider._poll_once(client) == provider._interval
    assert provider.get_prices()["AAPL"].price == 190.05


@pytest.mark.asyncio
async def test_rate_limit_backs_off():
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(429)) as client:
        assert await provider._poll_once(client) == RATE_LIMIT_BACKOFF


@pytest.mark.asyncio
async def test_bad_key_stops_polling():
    provider = MassiveProvider("bad")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(403)) as client:
        assert await provider._poll_once(client) is None
```

### 10.3 Interface conformance and factory

```python
import pytest

from backend.market.factory import make_provider
from backend.market.interface import MarketDataProvider
from backend.market.massive import MassiveProvider
from backend.market.simulator import SimulatorProvider


@pytest.mark.parametrize("cls", [SimulatorProvider, MassiveProvider])
def test_providers_implement_the_interface(cls):
    assert issubclass(cls, MarketDataProvider)
    assert not getattr(cls, "__abstractmethods__", None)
    assert cls.name in {"simulator", "massive"}


def test_factory_selects_simulator_without_a_key(monkeypatch):
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    assert isinstance(make_provider(), SimulatorProvider)


@pytest.mark.parametrize("value", ["", "   "])
def test_factory_treats_blank_keys_as_absent(monkeypatch, value):
    monkeypatch.setenv("MASSIVE_API_KEY", value)
    assert isinstance(make_provider(), SimulatorProvider)


def test_factory_selects_massive_with_a_key(monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "abc123")
    assert isinstance(make_provider(), MassiveProvider)
```

### 10.4 History and stream

```python
def test_history_ignores_repeated_timestamps():
    history = PriceHistory()
    update = PriceUpdate("AAPL", 190.0, 189.0, 0.5, 1000.0)
    history.record({"AAPL": update})
    history.record({"AAPL": update})
    assert len(history.get("AAPL")) == 1


def test_history_is_bounded():
    history = PriceHistory(max_points=3)
    for i in range(10):
        history.record({"AAPL": PriceUpdate("AAPL", 1.0 + i, 1.0, 0.0, float(i))})
    assert len(history.get("AAPL")) == 3


def test_stream_sends_a_full_snapshot_then_deltas(client):
    """First event carries every ticker; later events only what moved."""


def test_stream_resends_a_re_added_ticker_with_an_unchanged_timestamp(client):
    """Regression: a removed ticker must be dropped from `sent` even on a round
    where nothing else changed, or re-adding it at the same exchange timestamp
    is diffed away and the row never populates."""
```

---

## 11. Files

```
backend/market/
├── __init__.py
├── interface.py     PriceUpdate, MarketDataProvider
├── simulator.py     SimulatorProvider (default)
├── massive.py       MassiveProvider (MASSIVE_API_KEY)
├── history.py       PriceHistory + record_loop
├── tickers.py       normalize / normalize_all
├── tracking.py      tracked_tickers / refresh_tracked
└── factory.py       make_provider

backend/routes/
├── stream.py        GET /api/stream/prices
└── prices.py        GET /api/prices/{ticker}/history
```

---

## 12. Build order

Each step is independently verifiable — do not start the next until the current
one passes.

1. `interface.py` + `tickers.py` + their tests. No dependencies.
2. `simulator.py` + tests. Verify a standalone `asyncio.run` script prints moving
   prices.
3. `factory.py` + tests. Simulator path only; import Massive last.
4. Lifespan wiring + `GET /api/health`. Verify `tickers: 10`, `healthy: true`.
5. `stream.py`. Verify with `curl -N localhost:8000/api/stream/prices` — one large
   first event, then deltas.
6. `history.py` + `prices.py`. Verify the endpoint fills up over ~30 seconds.
7. `tracking.py` + `refresh_tracked` calls in the watchlist and trade routes.
   Verify a ticker added through the API starts streaming within one tick.
8. `massive.py` + tests. Ship last: it is optional, and every earlier step must
   work without an API key.
```
