# FinAlly — Finance Ally

## What This Is

An AI-powered trading workstation with a Bloomberg-terminal look: it streams live market data, lets the user trade a simulated $10,000 portfolio, and includes an LLM chat assistant that can analyze positions and execute trades and watchlist changes on the user's behalf. It is the capstone project for an agentic AI coding course, run as a single Docker container on port 8000 with no login. The full specification lives in `planning/PLAN.md`.

## Core Value

The user watches prices stream live, trades a simulated portfolio, and tells the AI assistant in natural language to analyze or trade it — all in one dense, dark terminal UI that starts with a single command.

## Requirements

### Validated

(None yet — a first implementation exists (commit `d3abe5e`) but has not been verified against PLAN.md. Requirements move here as phases verify them.)

### Active

Everything in `planning/PLAN.md` is in scope. Existing code is reused wherever it already satisfies a requirement; each phase verifies against the spec.

- [ ] Market data: simulator (GBM, correlated moves, random events, ~500ms) and optional Massive REST poller behind one interface, feeding a shared in-memory price cache
- [ ] SSE stream `GET /api/stream/prices` with ticker, price, previous price, timestamp, direction; auto-reconnect on the client
- [ ] SQLite with lazy init and seed data (default user with $10,000; 10 default tickers) at `db/finally.db`
- [ ] Portfolio API: positions, cash, total value, unrealized P&L; market-order trades (buy/sell, fractional shares, validation); value history from snapshots (at seed and after each trade)
- [ ] Watchlist API: list with latest prices, add, remove
- [ ] Chat API: LLM via LiteLLM → OpenRouter (Cerebras, structured output) with portfolio context and history; auto-executes trades and watchlist changes; errors reported in the reply; `LLM_MOCK=true` deterministic mode
- [ ] Health endpoint `GET /api/health`
- [ ] Frontend (Next.js static export, TypeScript, Tailwind, dark theme): watchlist with green/red price flash and sparklines, main chart for selected ticker, portfolio heatmap, P&L chart, positions table, trade bar, collapsible AI chat panel, header with live total value, cash and connection-status dot
- [ ] Single-container deployment: multi-stage Dockerfile (Node → Python/uv), FastAPI serving static files and API, named volume for the database
- [ ] Start/stop scripts for macOS/Linux and Windows, idempotent
- [ ] Tests: backend pytest (market, portfolio, LLM parsing, API routes), frontend unit tests, Playwright E2E with mock LLM covering the key scenarios in PLAN.md §12

### Out of Scope

- Limit orders, partial fills, order book — market orders only keeps portfolio math simple
- Authentication and multi-user — single-user app with no `user_id` columns (per `planning/DECISIONS.md`)
- Token-by-token LLM streaming — Cerebras is fast enough for a loading indicator
- Cloud deployment (Terraform / App Runner) — stretch goal, not part of the core build
- WebSocket transport — SSE is sufficient for one-way push

## Context

- Brownfield: the repo already contains a first implementation (`backend/`, `frontend/`, `scripts/`, `test/`, `Dockerfile`) and the market-data component is documented in `planning/MARKET_DATA_SUMMARY.md`. A codebase map is in `.planning/codebase/`, but its findings are unverified and mix real issues with invented details.
- `planning/PLAN.md` §13 raised review questions and simplifications; `planning/DECISIONS.md` already resolves them (SSE scoped to the watchlist, main chart and sparklines built from SSE only, Lightweight Charts, watchlist `add`/`remove`, no `user_id`, snapshot-on-trade only, `action_summary` text column, local E2E). Where DECISIONS.md and PLAN.md differ, DECISIONS.md wins.
- LLM calls use the `cerebras` skill (LiteLLM → OpenRouter → `openai/gpt-oss-120b` via Cerebras). `OPENROUTER_API_KEY` is in the root `.env`.
- Built by coding agents; agents coordinate through files in `planning/`.

## Constraints

- **Architecture**: Single container, single port (8000), FastAPI serving the Next.js static export — keeps deployment to one command
- **Tech stack**: Python/FastAPI managed with `uv`; Next.js + TypeScript + Tailwind; SQLite; SSE — per PLAN.md
- **Code style**: Simple, incremental, no over-engineering or defensive programming; short modules and functions; latest library APIs; concise docstrings
- **Debugging**: Identify and prove the root cause before fixing
- **Visual**: Dark theme (`#0d1117`/`#1a1a2e`), accent yellow `#ecad0a`, blue `#209dd7`, purple `#753991` for submit buttons; desktop-first

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SSE over WebSockets | One-way push is all that's needed | — Pending |
| Static Next.js export served by FastAPI | One origin, no CORS, one container | — Pending |
| SQLite, lazy init | No auth means no DB server needed; zero setup | — Pending |
| Market orders only | Removes order-book and partial-fill complexity | — Pending |
| Simulator by default, Massive API if key set | Works offline with no key | — Pending |
| LLM trades auto-execute with no confirmation | Fake money; fluid agentic demo | — Pending |
| Reuse existing implementation, verify per phase | User chose "build the whole plan, reuse code" over audit-only or rebuild | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-20 after initialization*
