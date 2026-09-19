"""Portfolio endpoints: view holdings, execute trades, view value history."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import repository
from portfolio.context import build_portfolio_context
from portfolio.trading import TradeError, execute_trade

router = APIRouter()


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str


@router.get("/portfolio")
async def get_portfolio(request: Request):
    provider = request.app.state.provider
    return build_portfolio_context(provider.get_prices())


@router.post("/portfolio/trade")
async def post_trade(payload: TradeRequest, request: Request):
    provider = request.app.state.provider
    try:
        return execute_trade(payload.ticker, payload.side, payload.quantity, provider.get_prices())
    except TradeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portfolio/history")
async def get_history():
    return repository.list_snapshots()
