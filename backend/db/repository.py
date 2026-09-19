"""Plain-function data access. No classes, no ORM — every function opens the
shared connection via `get_connection()` and commits its own writes.
"""

import uuid
from datetime import UTC, datetime

from db.connection import get_connection
from market.tickers import normalize


def _now() -> str:
    return datetime.now(UTC).isoformat()


# -- Profile ------------------------------------------------------------


def get_cash_balance() -> float:
    conn = get_connection()
    row = conn.execute("SELECT cash_balance FROM users_profile WHERE id = 1").fetchone()
    return row["cash_balance"]


def set_cash_balance(new_balance: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE users_profile SET cash_balance = ? WHERE id = 1", (new_balance,))
    conn.commit()


# -- Watchlist ------------------------------------------------------------


def list_watchlist() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at, rowid").fetchall()
    return [row["ticker"] for row in rows]


def add_watchlist_ticker(ticker: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO watchlist (id, ticker, added_at) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), normalize(ticker), _now()),
    )
    conn.commit()


def remove_watchlist_ticker(ticker: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM watchlist WHERE ticker = ?", (normalize(ticker),))
    conn.commit()


# -- Positions ------------------------------------------------------------


def list_positions() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT ticker, quantity, avg_cost, updated_at FROM positions ORDER BY ticker"
    ).fetchall()
    return [dict(row) for row in rows]


def get_position(ticker: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT ticker, quantity, avg_cost, updated_at FROM positions WHERE ticker = ?",
        (normalize(ticker),),
    ).fetchone()
    return dict(row) if row else None


def upsert_position(ticker: str, quantity: float, avg_cost: float) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO positions (id, ticker, quantity, avg_cost, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            quantity = excluded.quantity,
            avg_cost = excluded.avg_cost,
            updated_at = excluded.updated_at
        """,
        (str(uuid.uuid4()), normalize(ticker), quantity, avg_cost, _now()),
    )
    conn.commit()


def delete_position(ticker: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM positions WHERE ticker = ?", (normalize(ticker),))
    conn.commit()


# -- Trades ------------------------------------------------------------


def record_trade(ticker: str, side: str, quantity: float, price: float) -> str:
    conn = get_connection()
    trade_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO trades (id, ticker, side, quantity, price, executed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (trade_id, normalize(ticker), side, quantity, price, _now()),
    )
    conn.commit()
    return trade_id


# -- Portfolio snapshots ------------------------------------------------------------


def record_snapshot(total_value: float) -> str:
    conn = get_connection()
    snapshot_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO portfolio_snapshots (id, total_value, recorded_at) VALUES (?, ?, ?)",
        (snapshot_id, total_value, _now()),
    )
    conn.commit()
    return snapshot_id


def list_snapshots() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, total_value, recorded_at FROM portfolio_snapshots "
        "ORDER BY recorded_at, rowid"
    ).fetchall()
    return [dict(row) for row in rows]


# -- Chat ------------------------------------------------------------


def add_chat_message(role: str, content: str, action_summary: str | None = None) -> str:
    conn = get_connection()
    message_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO chat_messages (id, role, content, action_summary, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (message_id, role, content, action_summary, _now()),
    )
    conn.commit()
    return message_id


def list_recent_chat_messages(limit: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, role, content, action_summary, created_at FROM chat_messages "
        "ORDER BY created_at DESC, rowid DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]
