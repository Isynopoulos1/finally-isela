"""Chat endpoint: LLM conversation with auto-executed trades/watchlist changes."""

import os

from fastapi import APIRouter, Request
from openai import OpenAIError
from pydantic import BaseModel

from db import repository
from llm.client import call_llm
from llm.mock import mock_response
from llm.prompt import build_messages
from llm.schema import ChatCompletion, ChatTrade, WatchlistChange
from portfolio.context import build_portfolio_context
from portfolio.trading import TradeError, execute_trade

router = APIRouter()

HISTORY_LIMIT = 20


class ChatRequest(BaseModel):
    message: str


def _apply_trades(trades: list[ChatTrade], prices) -> list[dict]:
    results = []
    for trade in trades:
        try:
            execute_trade(trade.ticker, trade.side, trade.quantity, prices)
            results.append(
                {"ticker": trade.ticker, "side": trade.side, "quantity": trade.quantity, "status": "executed"}
            )
        except TradeError as exc:
            results.append(
                {
                    "ticker": trade.ticker,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "status": "failed",
                    "error": str(exc),
                }
            )
    return results


async def _apply_watchlist_changes(changes: list[WatchlistChange], provider) -> list[dict]:
    results = []
    for change in changes:
        ticker = change.ticker.strip().upper()
        current = repository.list_watchlist()
        if change.action == "add":
            if ticker in current:
                results.append({"ticker": ticker, "action": "add", "status": "already_present"})
                continue
            repository.add_watchlist_ticker(ticker)
            results.append({"ticker": ticker, "action": "add", "status": "executed"})
        else:
            if ticker not in current:
                results.append({"ticker": ticker, "action": "remove", "status": "not_present"})
                continue
            repository.remove_watchlist_ticker(ticker)
            results.append({"ticker": ticker, "action": "remove", "status": "executed"})

    if any(r["status"] == "executed" for r in results):
        await provider.update_tickers(repository.list_watchlist())
    return results


def _summarize(trade_results: list[dict], watchlist_results: list[dict]) -> str | None:
    parts = []
    for r in trade_results:
        if r["status"] == "executed":
            parts.append(f"{r['side'].capitalize()} {r['quantity']} {r['ticker']}")
        else:
            parts.append(f"Failed to {r['side']} {r['quantity']} {r['ticker']}: {r['error']}")
    for r in watchlist_results:
        if r["status"] == "executed":
            verb, prep = ("Added", "to") if r["action"] == "add" else ("Removed", "from")
            parts.append(f"{verb} {r['ticker']} {prep} watchlist")
    return "; ".join(parts) if parts else None


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request):
    provider = request.app.state.provider
    prices = provider.get_prices()

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in repository.list_recent_chat_messages(HISTORY_LIMIT)
    ]
    portfolio_context = build_portfolio_context(prices)

    if os.getenv("LLM_MOCK") == "true":
        completion = mock_response(payload.message)
    else:
        messages = build_messages(portfolio_context, history, payload.message)
        try:
            completion = call_llm(messages)
        except (OpenAIError, ValueError):
            completion = ChatCompletion(
                message="Sorry, I ran into a problem processing that. Please try again.",
            )

    trade_results = _apply_trades(completion.trades or [], prices)
    watchlist_results = await _apply_watchlist_changes(completion.watchlist_changes or [], provider)
    action_summary = _summarize(trade_results, watchlist_results)

    repository.add_chat_message("user", payload.message)
    repository.add_chat_message("assistant", completion.message, action_summary=action_summary)

    return {
        "message": completion.message,
        "trades": trade_results,
        "watchlist_changes": watchlist_results,
    }
