from unittest.mock import Mock

import pytest

from db import repository
from llm.schema import ChatCompletion, ChatTrade, WatchlistChange


@pytest.fixture
def mock_llm(monkeypatch):
    """Replace the real LLM call with a controllable mock and force live mode."""
    monkeypatch.delenv("LLM_MOCK", raising=False)
    mocked = Mock()
    monkeypatch.setattr("api.chat.call_llm", mocked)
    return mocked


def test_llm_mock_mode_is_deterministic_and_skips_network(api_client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    mocked = Mock()
    monkeypatch.setattr("api.chat.call_llm", mocked)

    response = api_client.post("/api/chat", json={"message": "hello there"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Mock response: hello there"
    assert body["trades"] == []
    assert body["watchlist_changes"] == []
    mocked.assert_not_called()


def test_llm_mock_mode_buy_trigger_phrase_executes_trade(api_client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    mocked = Mock()
    monkeypatch.setattr("api.chat.call_llm", mocked)

    response = api_client.post("/api/chat", json={"message": "buy 2 AAPL"})

    assert response.status_code == 200
    body = response.json()
    assert body["trades"] == [{"ticker": "AAPL", "side": "buy", "quantity": 2, "status": "executed"}]
    mocked.assert_not_called()
    portfolio = api_client.get("/api/portfolio").json()
    assert any(p["ticker"] == "AAPL" and p["quantity"] == 2 for p in portfolio["positions"])


def test_llm_mock_mode_watchlist_trigger_phrases(api_client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    monkeypatch.setattr("api.chat.call_llm", Mock())

    add_response = api_client.post("/api/chat", json={"message": "add PYPL to watchlist"})
    assert add_response.json()["watchlist_changes"] == [
        {"ticker": "PYPL", "action": "add", "status": "executed"}
    ]

    remove_response = api_client.post("/api/chat", json={"message": "remove PYPL from watchlist"})
    assert remove_response.json()["watchlist_changes"] == [
        {"ticker": "PYPL", "action": "remove", "status": "executed"}
    ]


def test_chat_executes_valid_trade(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Buying 1 share of AAPL for you.",
        trades=[ChatTrade(ticker="AAPL", side="buy", quantity=1)],
    )

    response = api_client.post("/api/chat", json={"message": "buy 1 AAPL"})

    assert response.status_code == 200
    body = response.json()
    assert body["trades"] == [
        {"ticker": "AAPL", "side": "buy", "quantity": 1, "status": "executed"}
    ]
    portfolio = api_client.get("/api/portfolio").json()
    assert any(p["ticker"] == "AAPL" for p in portfolio["positions"])


def test_chat_reports_failed_trade_without_crashing(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Selling GOOGL.",
        trades=[ChatTrade(ticker="GOOGL", side="sell", quantity=5)],
    )

    response = api_client.post("/api/chat", json={"message": "sell 5 GOOGL"})

    assert response.status_code == 200
    body = response.json()
    assert body["trades"][0]["status"] == "failed"
    assert "Insufficient shares" in body["trades"][0]["error"]


def test_chat_adds_and_removes_watchlist_ticker(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Updating your watchlist.",
        watchlist_changes=[
            WatchlistChange(ticker="PYPL", action="add"),
            WatchlistChange(ticker="NFLX", action="remove"),
        ],
    )

    response = api_client.post("/api/chat", json={"message": "swap NFLX for PYPL"})

    assert response.status_code == 200
    body = response.json()
    assert {"ticker": "PYPL", "action": "add", "status": "executed"} in body["watchlist_changes"]
    assert {"ticker": "NFLX", "action": "remove", "status": "executed"} in body["watchlist_changes"]
    watchlist = [entry["ticker"] for entry in api_client.get("/api/watchlist").json()]
    assert "PYPL" in watchlist
    assert "NFLX" not in watchlist


def test_chat_handles_llm_failure_gracefully(api_client, mock_llm):
    mock_llm.side_effect = ValueError("malformed structured output")

    response = api_client.post("/api/chat", json={"message": "what should I buy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["trades"] == []
    assert body["watchlist_changes"] == []
    assert "problem" in body["message"].lower()


def test_chat_persists_history_with_action_summary(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Done.",
        trades=[ChatTrade(ticker="AAPL", side="buy", quantity=1)],
    )

    api_client.post("/api/chat", json={"message": "buy 1 AAPL"})

    messages = repository.list_recent_chat_messages(10)
    assert messages[-2]["role"] == "user"
    assert messages[-2]["content"] == "buy 1 AAPL"
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "Done."
    assert "Buy 1.0 AAPL" in messages[-1]["action_summary"]
