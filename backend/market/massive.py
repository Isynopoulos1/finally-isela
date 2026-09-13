"""Massive (Polygon.io) REST provider — optional, selected when MASSIVE_API_KEY is set.

Polls the multi-ticker snapshot endpoint: one HTTP call covers the whole
tracked set, which keeps the free tier (5 req/min) comfortable at a
15-second interval. See planning/MASSIVE_API.md for the response shape.
"""

import asyncio
import logging
import os
import time
from contextlib import suppress

import httpx

from market.interface import MarketDataProvider, PriceUpdate

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
            log.error(
                "Massive rejected the API key (%d) — polling disabled. "
                "Unset MASSIVE_API_KEY to use the simulator.",
                resp.status_code,
            )
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
