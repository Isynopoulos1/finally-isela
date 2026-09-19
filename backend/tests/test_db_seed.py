import sqlite3

from db.schema import init_db
from db.seed import DEFAULT_CASH_BALANCE, DEFAULT_TICKERS, seed


def _fresh_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_seed_inserts_default_profile_watchlist_and_snapshot():
    conn = _fresh_conn()
    seed(conn)

    balance = conn.execute("SELECT cash_balance FROM users_profile WHERE id = 1").fetchone()
    assert balance["cash_balance"] == DEFAULT_CASH_BALANCE

    tickers = [r["ticker"] for r in conn.execute("SELECT ticker FROM watchlist").fetchall()]
    assert set(tickers) == set(DEFAULT_TICKERS)
    assert len(tickers) == 10

    snapshots = conn.execute("SELECT total_value FROM portfolio_snapshots").fetchall()
    assert len(snapshots) == 1
    assert snapshots[0]["total_value"] == DEFAULT_CASH_BALANCE


def test_seed_runs_once():
    conn = _fresh_conn()
    seed(conn)

    conn.execute("UPDATE users_profile SET cash_balance = 42.0 WHERE id = 1")
    conn.commit()

    seed(conn)  # must be a no-op — profile already exists

    balance = conn.execute("SELECT cash_balance FROM users_profile WHERE id = 1").fetchone()
    assert balance["cash_balance"] == 42.0

    count = conn.execute("SELECT COUNT(*) AS n FROM watchlist").fetchone()
    assert count["n"] == 10
