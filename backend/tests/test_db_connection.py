from db import connection


def test_get_connection_lazily_initializes_and_seeds(tmp_path, db_conn):
    row = db_conn.execute("SELECT cash_balance FROM users_profile WHERE id = 1").fetchone()
    assert row["cash_balance"] == 10000.0


def test_get_connection_returns_cached_connection_for_same_path(db_conn):
    assert connection.get_connection() is db_conn


def test_get_connection_reopens_on_new_path(tmp_path, db_conn):
    other = connection.get_connection(tmp_path / "other.db")
    assert other is not db_conn
    connection.close_connection()
