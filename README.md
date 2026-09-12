# FinAlly — AI Trading Workstation

A Bloomberg-style trading terminal with a live market data feed and an AI assistant that can analyze your portfolio and execute trades on your behalf. Built as a capstone for an agentic AI coding course.

## What it does

- Streams live (simulated) prices for a default watchlist of 10 tickers with green/red flash animations and sparkline charts
- Lets you buy and sell shares with instant market-order fills against a $10,000 virtual cash balance
- Shows a portfolio heatmap (treemap), P&L chart, and positions table
- Includes an AI chat panel powered by a fast LLM that can explain your portfolio, suggest trades, and execute them for you

## Quick start

```bash
cp .env.example .env          # add your OPENROUTER_API_KEY
./scripts/start_mac.sh        # builds image and opens http://localhost:8000
```

Windows: use `scripts/start_windows.ps1` in PowerShell.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | For the AI chat assistant |
| `MASSIVE_API_KEY` | No | Real market data via Polygon; omit to use the built-in simulator |
| `LLM_MOCK` | No | Set `true` for deterministic responses in tests |

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (TypeScript), static export, Tailwind CSS |
| Backend | FastAPI (Python), served via `uv` |
| Database | SQLite (auto-initialized, volume-mounted) |
| Real-time | Server-Sent Events (`/api/stream/prices`) |
| AI | LiteLLM → OpenRouter → Cerebras inference |
| Deploy | Single Docker container on port 8000 |

## Project layout

```
frontend/   Next.js app
backend/    FastAPI app (owns DB, SSE, LLM, market data)
planning/   Shared agent documentation (PLAN.md)
scripts/    start/stop Docker helpers
test/       Playwright E2E tests
db/         Runtime SQLite volume mount (finally.db gitignored)
```

## Stopping

```bash
./scripts/stop_mac.sh   # stops container; data volume is preserved
```
