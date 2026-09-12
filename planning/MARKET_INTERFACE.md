# Market Data Interface

## Design Goal

A single Python interface that both the **Massive API client** and the **price simulator** implement.  
The backend selects which to use at startup based on `MASSIVE_API_KEY`:

```python
# backend/market/factory.py
import os
from backend.market.interface import MarketDataProvider
from backend.market.massive import MassiveProvider
from backend.market.simulator import SimulatorProvider

def make_provider() -> MarketDataProvider:
    api_key = os.getenv("MASSIVE_API_KEY", "").strip()
    if api_key:
        return MassiveProvider(api_key)
    return SimulatorProvider()
```

All downstream code (SSE stream, price cache, portfolio valuation) uses only the interface — it never cares which backend is active.

---

## Abstract Interface

```python
# backend/market/interface.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class PriceUpdate:
    ticker: str
    price: float
    prev_price: float        # last price before this update
    change_pct: float        # (price - prev_close) / prev_close * 100
    timestamp: float         # Unix seconds (float)

class MarketDataProvider(ABC):

    @abstractmethod
    async def start(self, tickers: list[str]) -> None:
        """Begin generating price data for the given ticker list.

        Called once at startup. The provider may launch background tasks here.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Shut down any background tasks cleanly."""

    @abstractmethod
    def get_prices(self) -> dict[str, PriceUpdate]:
        """Return the latest PriceUpdate for every tracked ticker.

        Synchronous — callers read from an in-memory cache. Returns an
        empty dict if no data is available yet.
        """

    @abstractmethod
    async def update_tickers(self, tickers: list[str]) -> None:
        """Replace the tracked ticker list at runtime (watchlist changes)."""
```

---

## Massive Provider

```python
# backend/market/massive.py
import asyncio
import logging
import os
import time
from backend.market.interface import MarketDataProvider, PriceUpdate
import httpx

log = logging.getLogger(__name__)

BASE = "https://api.massive.com"
DEFAULT_POLL_INTERVAL = float(os.getenv("MASSIVE_POLL_INTERVAL_SECONDS", "15"))


class MassiveProvider(MarketDataProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._tickers: list[str] = []
        self._cache: dict[str, PriceUpdate] = {}
        self._task: asyncio.Task | None = None

    async def start(self, tickers: list[str]) -> None:
        self._tickers = tickers
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    def get_prices(self) -> dict[str, PriceUpdate]:
        return dict(self._cache)

    async def update_tickers(self, tickers: list[str]) -> None:
        self._tickers = tickers

    async def _poll_loop(self) -> None:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    await self._fetch_and_update(client)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    log.error("Massive poll error: %s", e)
                await asyncio.sleep(DEFAULT_POLL_INTERVAL)

    async def _fetch_and_update(self, client: httpx.AsyncClient) -> None:
        if not self._tickers:
            return
        params = {
            "tickers": ",".join(self._tickers),
            "apiKey": self._api_key,
        }
        resp = await client.get(
            f"{BASE}/v2/snapshot/locale/us/markets/stocks/tickers",
            params=params,
            timeout=10,
        )
        if resp.status_code == 429:
            log.warning("Massive rate limit — sleeping 60s")
            await asyncio.sleep(60)
            return
        resp.raise_for_status()

        now = time.time()
        for snap in resp.json().get("tickers", []):
            ticker = snap["ticker"]
            price = snap["lastTrade"]["p"]
            prev_close = snap.get("prevDay", {}).get("c", price)
            change_pct = snap.get("todaysChangePerc", 0.0)

            old = self._cache.get(ticker)
            prev_price = old.price if old else prev_close

            self._cache[ticker] = PriceUpdate(
                ticker=ticker,
                price=price,
                prev_price=prev_price,
                change_pct=change_pct,
                timestamp=now,
            )
```

---

## Simulator Provider

See `MARKET_SIMULATOR.md` for full design. The provider wraps the simulator loop:

```python
# backend/market/simulator.py  (abbreviated — full code in MARKET_SIMULATOR.md)
from backend.market.interface import MarketDataProvider, PriceUpdate

class SimulatorProvider(MarketDataProvider):
    async def start(self, tickers: list[str]) -> None: ...
    async def stop(self) -> None: ...
    def get_prices(self) -> dict[str, PriceUpdate]: ...
    async def update_tickers(self, tickers: list[str]) -> None: ...
```

---

## Price Cache and SSE Integration

The FastAPI app holds one provider instance as application state. The SSE endpoint reads from it:

```python
# backend/main.py (startup)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.market.factory import make_provider
from backend.db import get_watchlist

@asynccontextmanager
async def lifespan(app: FastAPI):
    tickers = await get_watchlist()
    app.state.market = make_provider()
    await app.state.market.start(tickers)
    yield
    await app.state.market.stop()

app = FastAPI(lifespan=lifespan)
```

```python
# backend/routes/stream.py
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse
import json, time

async def price_stream(request: Request):
    provider = request.app.state.market

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            prices = provider.get_prices()
            if prices:
                payload = json.dumps({
                    ticker: {
                        "price": p.price,
                        "prev_price": p.prev_price,
                        "change_pct": p.change_pct,
                        "timestamp": p.timestamp,
                    }
                    for ticker, p in prices.items()
                })
                yield f"data: {payload}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Watchlist Change Propagation

When the user adds or removes a ticker, the API route updates the provider:

```python
# After DB update in POST /api/watchlist or DELETE /api/watchlist/{ticker}
all_tickers = await get_watchlist()
await request.app.state.market.update_tickers(all_tickers)
```

The simulator starts tracking the new ticker immediately (seeding a realistic start price).  
The Massive provider includes the new ticker on its next poll cycle.

---

## PriceUpdate Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | str | Stock symbol, e.g. `"AAPL"` |
| `price` | float | Latest price |
| `prev_price` | float | Price from the previous update (for flash direction) |
| `change_pct` | float | % change from previous close |
| `timestamp` | float | Unix seconds when this update was recorded |
