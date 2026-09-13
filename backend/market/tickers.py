"""Ticker symbol normalisation.

Everything upstream (DB, chat, API routes) must hand providers uppercase,
whitespace-stripped symbols. These helpers are the single entry point.
"""


def normalize(raw: str) -> str:
    """'  aapl ' -> 'AAPL'."""
    return raw.strip().upper()


def normalize_all(raw: list[str]) -> list[str]:
    """Normalise, drop blanks, de-duplicate, preserve order."""
    seen: dict[str, None] = {}
    for item in raw:
        ticker = normalize(item)
        if ticker:
            seen[ticker] = None
    return list(seen)
