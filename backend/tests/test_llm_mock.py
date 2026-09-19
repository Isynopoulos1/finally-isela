from llm.mock import mock_response


def test_buy_trigger_phrase():
    result = mock_response("buy 5 AAPL")
    assert result.trades[0].ticker == "AAPL"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 5
    assert result.watchlist_changes is None


def test_sell_trigger_phrase_is_case_insensitive():
    result = mock_response("Sell 1.5 tsla")
    assert result.trades[0] == mock_response("sell 1.5 TSLA").trades[0]
    assert result.trades[0].side == "sell"
    assert result.trades[0].ticker == "TSLA"
    assert result.trades[0].quantity == 1.5


def test_add_to_watchlist_trigger_phrase():
    result = mock_response("add pypl to watchlist")
    assert result.watchlist_changes[0].ticker == "PYPL"
    assert result.watchlist_changes[0].action == "add"
    assert result.trades is None


def test_remove_from_watchlist_trigger_phrase():
    result = mock_response("remove NFLX from watchlist")
    assert result.watchlist_changes[0].ticker == "NFLX"
    assert result.watchlist_changes[0].action == "remove"


def test_non_matching_message_falls_back_to_plain_echo():
    result = mock_response("what's my portfolio worth?")
    assert result.message == "Mock response: what's my portfolio worth?"
    assert result.trades is None
    assert result.watchlist_changes is None


def test_trade_phrase_with_extra_words_does_not_match():
    result = mock_response("please buy 5 AAPL for me")
    assert result.trades is None
    assert result.message.startswith("Mock response:")
