"""Structured-output schema for the LLM chat response."""

from typing import Literal

from pydantic import BaseModel


class ChatTrade(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


class WatchlistChange(BaseModel):
    ticker: str
    action: Literal["add", "remove"]


class ChatCompletion(BaseModel):
    message: str
    trades: list[ChatTrade] | None = None
    watchlist_changes: list[WatchlistChange] | None = None
