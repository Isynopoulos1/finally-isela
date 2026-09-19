import sqlite3

import pytest

from db import repository as repo


def test_get_and_set_cash_balance(db_conn):
    assert repo.get_cash_balance() == 10000.0
    repo.set_cash_balance(9500.5)
    assert repo.get_cash_balance() == 9500.5


def test_list_watchlist_has_default_tickers(db_conn):
    tickers = repo.list_watchlist()
    assert len(tickers) == 10
    assert "AAPL" in tickers


def test_add_watchlist_ticker_normalizes(db_conn):
    repo.add_watchlist_ticker("  pypl ")
    assert "PYPL" in repo.list_watchlist()


def test_add_watchlist_ticker_duplicate_raises(db_conn):
    with pytest.raises(sqlite3.IntegrityError):
        repo.add_watchlist_ticker("aapl")


def test_remove_watchlist_ticker(db_conn):
    repo.remove_watchlist_ticker("aapl")
    assert "AAPL" not in repo.list_watchlist()


def test_remove_watchlist_ticker_missing_is_a_noop(db_conn):
    repo.remove_watchlist_ticker("NOPE")  # must not raise
    assert len(repo.list_watchlist()) == 10


def test_position_round_trip(db_conn):
    assert repo.get_position("AAPL") is None

    repo.upsert_position("aapl", 10, 190.5)
    position = repo.get_position("AAPL")
    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 10
    assert position["avg_cost"] == 190.5

    repo.upsert_position("aapl", 15, 195.0)
    position = repo.get_position("AAPL")
    assert position["quantity"] == 15
    assert position["avg_cost"] == 195.0

    assert len(repo.list_positions()) == 1

    repo.delete_position("aapl")
    assert repo.get_position("AAPL") is None


def test_position_unique_constraint_bypassed_by_upsert(db_conn):
    repo.upsert_position("MSFT", 1, 400.0)
    repo.upsert_position("MSFT", 2, 410.0)  # must not raise — it's an upsert
    assert len(repo.list_positions()) == 1


def test_record_trade(db_conn):
    trade_id = repo.record_trade("tsla", "buy", 5, 250.0)
    assert isinstance(trade_id, str)


def test_snapshot_round_trip(db_conn):
    repo.record_snapshot(10500.0)
    snapshots = repo.list_snapshots()
    assert len(snapshots) == 2  # one from seed, one just recorded
    assert snapshots[-1]["total_value"] == 10500.0


def test_chat_message_round_trip(db_conn):
    repo.add_chat_message("user", "What's my P&L?")
    repo.add_chat_message("assistant", "Up $500 today.", action_summary="Bought 10 AAPL")

    messages = repo.list_recent_chat_messages(10)
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["action_summary"] == "Bought 10 AAPL"


def test_list_recent_chat_messages_respects_limit_and_order(db_conn):
    for i in range(5):
        repo.add_chat_message("user", f"message {i}")

    messages = repo.list_recent_chat_messages(2)
    assert [m["content"] for m in messages] == ["message 3", "message 4"]
