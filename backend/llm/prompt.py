"""System prompt and message-list construction for the chat endpoint."""

import json

SYSTEM_PROMPT = (
    "You are FinAlly, an AI trading assistant for a simulated brokerage account. "
    "Analyze the user's portfolio composition, risk concentration, and P&L. Suggest "
    "trades with clear reasoning. Execute trades when the user asks for them or agrees "
    "to a suggestion. Manage the watchlist proactively. Be concise and data-driven. "
    "Always respond using the structured schema you were given."
)


def build_messages(portfolio_context: dict, history: list[dict], user_message: str) -> list[dict]:
    """System prompt + portfolio snapshot + recent history + the new user message."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current portfolio state (JSON): {json.dumps(portfolio_context)}"},
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
