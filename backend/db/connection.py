"""Lazily-initialized SQLite connection, shared by the repository module.

The database file lives at `db/finally.db` under the project root (the
documented Docker volume mount point). Call `get_connection(path)` once with
an explicit path to point at a different file (tests use this with `tmp_path`).
"""

import sqlite3
from pathlib import Path

from db.schema import init_db
from db.seed import seed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "finally.db"

_db_path = DEFAULT_DB_PATH
_connection: sqlite3.Connection | None = None


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Return the shared connection, opening + initializing + seeding it on first use."""
    global _db_path, _connection

    if db_path is not None:
        _db_path = Path(db_path)
        close_connection()

    if _connection is None:
        _db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(_db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        seed(conn)
        _connection = conn

    return _connection


def close_connection() -> None:
    """Close the cached connection, if any. Tests use this to isolate cases."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
