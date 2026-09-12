# Massive API (formerly Polygon.io) — Reference

## Overview

Massive (rebranded from Polygon.io in late 2025) provides REST and WebSocket market data APIs for US stocks, options, forex, crypto, and futures.

- Base URL: `https://api.massive.com` (legacy `https://api.polygon.io` still works)
- Auth: `apiKey` query parameter on every request
- Free tier: **5 requests/minute**
- Paid tiers: unlimited requests, faster polling

Official docs: https://massive.com/docs  
Python client: https://github.com/massive-com/client-python

---

## Endpoints Used in This Project

### 1. Snapshot — Multiple Tickers

**Best endpoint for bulk price polling.** Returns current price, last trade, last quote, day OHLCV, and previous-day data for any number of tickers in one call.

```
GET https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers
```

**Parameters**

| Name     | Type   | Required | Description |
|----------|--------|----------|-------------|
| `tickers`| string | no       | Comma-separated list, e.g. `AAPL,TSLA,NVDA`. Omit for all ~10k tickers. |
| `apiKey` | string | yes      | Your API key |

**Example request**

```python
import httpx

BASE = "https://api.massive.com"

def get_snapshots(tickers: list[str], api_key: str) -> dict:
    params = {
        "tickers": ",".join(tickers),
        "apiKey": api_key,
    }
    resp = httpx.get(f"{BASE}/v2/snapshot/locale/us/markets/stocks/tickers", params=params)
    resp.raise_for_status()
    return resp.json()
```

**Response shape**

```json
{
  "status": "OK",
  "count": 3,
  "tickers": [
    {
      "ticker": "AAPL",
      "todaysChangePerc": 0.82,
      "todaysChange": 1.55,
      "updated": 1720000000000000000,
      "day": {
        "o": 188.50,
        "h": 191.20,
        "l": 187.90,
        "c": 190.05,
        "v": 52341200,
        "vw": 189.44
      },
      "lastTrade": {
        "p": 190.05,
        "s": 100,
        "t": 1720000000000000000,
        "x": 4
      },
      "lastQuote": {
        "P": 190.10,
        "S": 3,
        "p": 190.05,
        "s": 5,
        "t": 1720000000000000000
      },
      "prevDay": {
        "o": 187.80,
        "h": 189.60,
        "l": 186.50,
        "c": 188.50,
        "v": 49200000,
        "vw": 188.00
      },
      "min": {
        "o": 189.90,
        "h": 190.20,
        "l": 189.80,
        "c": 190.05,
        "v": 12400,
        "vw": 190.00,
        "t": 1720000000000
      }
    }
  ]
}
```

**Key fields to extract for this project**

| Field | Path | Meaning |
|-------|------|---------|
| Current price | `lastTrade.p` | Last trade price |
| Previous close | `prevDay.c` | Previous day close (for % change) |
| Day change % | `todaysChangePerc` | Precomputed daily change |
| Timestamp | `updated` | Nanoseconds since epoch |

---

### 2. Previous Close — Single Ticker

Returns the previous trading day's OHLCV for one ticker. Useful during pre-market hours before `lastTrade` is populated.

```
GET https://api.massive.com/v2/aggs/ticker/{ticker}/prev
```

**Parameters**

| Name       | Type   | Required | Description |
|------------|--------|----------|-------------|
| `ticker`   | path   | yes      | Stock symbol |
| `adjusted` | bool   | no       | Adjust for splits (default `true`) |
| `apiKey`   | string | yes      | Your API key |

**Example request**

```python
def get_previous_close(ticker: str, api_key: str) -> dict:
    params = {"adjusted": "true", "apiKey": api_key}
    resp = httpx.get(
        f"{BASE}/v2/aggs/ticker/{ticker}/prev",
        params=params,
    )
    resp.raise_for_status()
    data = resp.json()
    # results is a list with one item
    return data["results"][0]
```

**Response shape**

```json
{
  "ticker": "AAPL",
  "queryCount": 1,
  "resultsCount": 1,
  "adjusted": true,
  "results": [
    {
      "T": "AAPL",
      "v": 49200000,
      "vw": 188.00,
      "o": 187.80,
      "c": 188.50,
      "h": 189.60,
      "l": 186.50,
      "t": 1719878400000,
      "n": 412000
    }
  ],
  "status": "OK",
  "request_id": "abc123"
}
```

---

## Official Python Client (Optional)

Massive ships a first-party Python client that wraps all REST endpoints.

```
pip install massive
```

```python
from massive import RESTClient

client = RESTClient(api_key="YOUR_KEY")

# Snapshot for multiple tickers
snapshots = client.get_snapshot_all("stocks", tickers=["AAPL", "TSLA", "NVDA"])
for snap in snapshots:
    print(snap.ticker, snap.last_trade.price)

# Single ticker snapshot
snap = client.get_snapshot_ticker("stocks", "AAPL")
print(snap.last_trade.price)
```

For this project we use `httpx` directly (already in the backend dependency tree) rather than adding the `massive` SDK, keeping the dependency surface small.

---

## Rate Limits and Polling Strategy

| Plan    | Requests/min | Recommended poll interval |
|---------|-------------|--------------------------|
| Free    | 5           | 15 s (one snapshot call per poll) |
| Starter | unlimited   | 5 s |
| Advanced| unlimited   | 2 s |

**Polling strategy for this project:**
- One call to the snapshot endpoint covering all watchlist tickers
- Poll interval defaults to **15 seconds** (safe for free tier)
- Configurable via `MASSIVE_POLL_INTERVAL_SECONDS` env var

---

## Error Handling

The API returns HTTP 4xx/5xx on errors. Common cases:

| HTTP | Meaning | Action |
|------|---------|--------|
| 429  | Rate limit exceeded | Backoff and retry after 60 s |
| 403  | Invalid/missing API key | Log and disable polling |
| 404  | Ticker not found | Skip ticker, log warning |

```python
import httpx
import logging

log = logging.getLogger(__name__)

def safe_snapshot(tickers: list[str], api_key: str) -> list[dict]:
    try:
        data = get_snapshots(tickers, api_key)
        return data.get("tickers", [])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            log.warning("Massive rate limit hit — backing off")
        else:
            log.error("Massive API error: %s", e)
        return []
```

---

## Market Hours

Snapshot data reflects real-time prices during market hours (9:30 AM – 4:00 PM ET).  
Outside market hours `lastTrade.p` reflects the most recent extended-hours price.  
Snapshot cache resets daily at 3:30 AM ET; data repopulates from ~4:00 AM ET.
