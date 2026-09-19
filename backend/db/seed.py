"""Default seed data, inserted once when `users_profile` is empty."""

import sqlite3
import uuid
from datetime import UTC, datetime

DEFAULT_CASH_BALANCE = 10000.0
DEFAULT_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]


def seed(conn: sqlite3.Connection) -> None:
    """Insert the default profile, watchlist, and starting snapshot if not already seeded."""
    if conn.execute("SELECT 1 FROM users_profile").fetchone() is not None:
        return

    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (1, ?, ?)",
        (DEFAULT_CASH_BALANCE, now),
    )
    conn.executemany(
        "INSERT INTO watchlist (id, ticker, added_at) VALUES (?, ?, ?)",
        [(str(uuid.uuid4()), ticker, now) for ticker in DEFAULT_TICKERS],
    )
    conn.execute(
        "INSERT INTO portfolio_snapshots (id, total_value, recorded_at) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), DEFAULT_CASH_BALANCE, now),
    )
    conn.commit()
