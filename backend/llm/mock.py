"""Deterministic mock chat response used when LLM_MOCK=true.

Recognizes a few fixed trigger phrases so E2E tests can exercise the real
trade/watchlist execution path without a network call:

  - "buy <quantity> <ticker>" / "sell <quantity> <ticker>" -> one trade
  - "add <ticker> to watchlist" -> one watchlist add
  - "remove <ticker> from watchlist" -> one watchlist remove

Anything else falls back to a plain echo with no trades/watchlist changes.
Matching is case-insensitive and matches the whole message (surrounding
whitespace is stripped first).
"""

import re

from llm.schema import ChatCompletion, ChatTrade, WatchlistChange

_TRADE_RE = re.compile(r"^(buy|sell)\s+(\d+(?:\.\d+)?)\s+([a-zA-Z]{1,10})$", re.IGNORECASE)
_WATCHLIST_ADD_RE = re.compile(r"^add\s+([a-zA-Z]{1,10})\s+to\s+watchlist$", re.IGNORECASE)
_WATCHLIST_REMOVE_RE = re.compile(r"^remove\s+([a-zA-Z]{1,10})\s+from\s+watchlist$", re.IGNORECASE)


def mock_response(user_message: str) -> ChatCompletion:
    text = user_message.strip()

    trade_match = _TRADE_RE.match(text)
    if trade_match:
        side, quantity, ticker = trade_match.groups()
        side, ticker = side.lower(), ticker.upper()
        return ChatCompletion(
            message=f"Mock: {side}ing {quantity} {ticker}.",
            trades=[ChatTrade(ticker=ticker, side=side, quantity=float(quantity))],
        )

    add_match = _WATCHLIST_ADD_RE.match(text)
    if add_match:
        ticker = add_match.group(1).upper()
        return ChatCompletion(
            message=f"Mock: adding {ticker} to your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="add")],
        )

    remove_match = _WATCHLIST_REMOVE_RE.match(text)
    if remove_match:
        ticker = remove_match.group(1).upper()
        return ChatCompletion(
            message=f"Mock: removing {ticker} from your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="remove")],
        )

    return ChatCompletion(message=f"Mock response: {user_message}")
