"""Market-order execution — shared by the manual trade route and the LLM
engineer's auto-executed chat trades.
"""

from db import repository
from market.interface import PriceUpdate
from market.tickers import normalize
from portfolio.context import build_portfolio_context

MIN_QUANTITY = 1e-9


class TradeError(Exception):
    """Validation failure. Message is safe to show directly to the user."""


def execute_trade(ticker: str, side: str, quantity: float, prices: dict[str, PriceUpdate]) -> dict:
    """Validate and execute a market order, then return the updated portfolio context.

    `prices` is the market provider's current price cache (`provider.get_prices()`).
    Raises `TradeError` on any validation failure (bad side, non-positive quantity,
    unpriced ticker, insufficient cash, or insufficient shares).
    """
    ticker = normalize(ticker)
    if side not in ("buy", "sell"):
        raise TradeError(f"Invalid side '{side}': must be 'buy' or 'sell'")
    if quantity <= 0:
        raise TradeError("Quantity must be positive")

    update = prices.get(ticker)
    if update is None:
        raise TradeError(f"No live price available for {ticker}")
    price = update.price

    position = repository.get_position(ticker)

    if side == "buy":
        cost = quantity * price
        cash = repository.get_cash_balance()
        if cost > cash:
            raise TradeError(f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}")
        if position:
            new_quantity = position["quantity"] + quantity
            new_avg_cost = (position["quantity"] * position["avg_cost"] + cost) / new_quantity
        else:
            new_quantity, new_avg_cost = quantity, price
        repository.upsert_position(ticker, new_quantity, new_avg_cost)
        repository.set_cash_balance(cash - cost)
    else:
        owned = position["quantity"] if position else 0.0
        if quantity > owned:
            raise TradeError(f"Insufficient shares: trying to sell {quantity}, own {owned}")
        proceeds = quantity * price
        remaining = owned - quantity
        if remaining > MIN_QUANTITY:
            repository.upsert_position(ticker, remaining, position["avg_cost"])
        else:
            repository.delete_position(ticker)
        repository.set_cash_balance(repository.get_cash_balance() + proceeds)

    repository.record_trade(ticker, side, quantity, price)

    context = build_portfolio_context(prices)
    repository.record_snapshot(context["total_value"])
    return context
