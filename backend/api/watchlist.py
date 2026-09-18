"""Watchlist endpoints: list, add, remove tickers."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import repository
from market.interface import PriceUpdate
from market.tickers import normalize

router = APIRouter()


class WatchlistRequest(BaseModel):
    ticker: str


def _entries(prices: dict[str, PriceUpdate]) -> list[dict]:
    entries = []
    for ticker in repository.list_watchlist():
        update = prices.get(ticker)
        entries.append(
            {
                "ticker": ticker,
                "price": update.price if update else None,
                "prev_price": update.prev_price if update else None,
                "change_pct": update.change_pct if update else None,
            }
        )
    return entries


@router.get("/watchlist")
async def get_watchlist(request: Request):
    provider = request.app.state.provider
    return _entries(provider.get_prices())


@router.post("/watchlist")
async def add_ticker(payload: WatchlistRequest, request: Request):
    ticker = normalize(payload.ticker)
    if ticker in repository.list_watchlist():
        raise HTTPException(status_code=400, detail=f"{ticker} is already on the watchlist")
    repository.add_watchlist_ticker(ticker)
    provider = request.app.state.provider
    await provider.update_tickers(repository.list_watchlist())
    return _entries(provider.get_prices())


@router.delete("/watchlist/{ticker}")
async def remove_ticker(ticker: str, request: Request):
    ticker = normalize(ticker)
    if ticker not in repository.list_watchlist():
        raise HTTPException(status_code=404, detail=f"{ticker} is not on the watchlist")
    repository.remove_watchlist_ticker(ticker)
    provider = request.app.state.provider
    await provider.update_tickers(repository.list_watchlist())
    return _entries(provider.get_prices())
