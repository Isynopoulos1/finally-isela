import pytest
from pydantic import ValidationError

from llm.schema import ChatCompletion


def test_parses_full_valid_schema():
    raw = (
        '{"message": "Buying AAPL.", '
        '"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}], '
        '"watchlist_changes": [{"ticker": "PYPL", "action": "add"}]}'
    )
    parsed = ChatCompletion.model_validate_json(raw)
    assert parsed.message == "Buying AAPL."
    assert parsed.trades[0].ticker == "AAPL"
    assert parsed.trades[0].side == "buy"
    assert parsed.watchlist_changes[0].action == "add"


def test_message_only_defaults_missing_fields_to_none():
    parsed = ChatCompletion.model_validate_json('{"message": "Just chatting."}')
    assert parsed.trades is None
    assert parsed.watchlist_changes is None


def test_watchlist_remove_action_supported():
    parsed = ChatCompletion.model_validate_json(
        '{"message": "ok", "watchlist_changes": [{"ticker": "TSLA", "action": "remove"}]}'
    )
    assert parsed.watchlist_changes[0].action == "remove"


def test_invalid_trade_side_rejected():
    with pytest.raises(ValidationError):
        ChatCompletion.model_validate_json(
            '{"message": "x", "trades": [{"ticker": "AAPL", "side": "hold", "quantity": 1}]}'
        )


def test_missing_message_field_rejected():
    with pytest.raises(ValidationError):
        ChatCompletion.model_validate_json('{"trades": []}')
