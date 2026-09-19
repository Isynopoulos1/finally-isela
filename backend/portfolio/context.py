"""Portfolio snapshot: cash, live-priced positions, and watchlist.

Shared by the `/api/portfolio` route and the LLM engineer's chat prompt
builder — both need the same view of the user's current state.
"""

from db import repository
from market.interface import PriceUpdate


def _current_price(ticker: str, prices: dict[str, PriceUpdate], fallback: float) -> float:
    """Live price if the ticker has one cached, else `fallback` (e.g. avg_cost)."""
    update = prices.get(ticker)
    return update.price if update else fallback


def build_portfolio_context(prices: dict[str, PriceUpdate]) -> dict:
    """Cash, positions (with live P&L), watchlist, and total portfolio value.

    `prices` is the market provider's current cache (`provider.get_prices()`).
    """
    cash_balance = repository.get_cash_balance()

    positions = []
    positions_value = 0.0
    for position in repository.list_positions():
        ticker = position["ticker"]
        current_price = _current_price(ticker, prices, position["avg_cost"])
        market_value = position["quantity"] * current_price
        cost_basis = position["quantity"] * position["avg_cost"]
        positions_value += market_value
        positions.append(
            {
                "ticker": ticker,
                "quantity": position["quantity"],
                "avg_cost": position["avg_cost"],
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(market_value - cost_basis, 2),
                "unrealized_pnl_pct": round(
                    (current_price - position["avg_cost"]) / position["avg_cost"] * 100, 3
                ),
            }
        )

    watchlist = []
    for ticker in repository.list_watchlist():
        update = prices.get(ticker)
        watchlist.append(
            {
                "ticker": ticker,
                "price": update.price if update else None,
                "prev_price": update.prev_price if update else None,
                "change_pct": update.change_pct if update else None,
            }
        )

    return {
        "cash_balance": cash_balance,
        "positions": positions,
        "watchlist": watchlist,
        "total_value": round(cash_balance + positions_value, 2),
    }
