# Roadmap: FinAlly

## Overview

FinAlly is built as six vertical slices, each one adding a capability the user can see in the browser. The repo already contains a first implementation, so every phase starts by verifying the existing `backend/`, `frontend/`, `scripts/` and `test/` code against PLAN.md and then fixes or completes it — no phase assumes the current code is correct. The journey goes from "one command starts the app with a seeded database", through "prices stream live in a dark terminal UI" and "the user curates a watchlist and inspects a ticker", to "the user trades a simulated $10,000 portfolio" and "the AI assistant analyzes and trades on their behalf", closing with a proven end-to-end demo path.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: One-Command Start** - App boots from a single command with a seeded, persistent database
- [ ] **Phase 2: Live Prices Streaming** - Ten tickers tick live in the dark terminal UI with flashes and sparklines
- [ ] **Phase 3: Watchlist Control & Ticker Detail** - User curates watched tickers and drills into one on the main chart
- [ ] **Phase 4: Portfolio & Trading** - User trades the simulated $10,000 and watches the portfolio respond
- [ ] **Phase 5: AI Trading Assistant** - Chat analyzes the portfolio and executes trades and watchlist changes
- [ ] **Phase 6: Ship-Ready Verification** - The full demo journey is proven green in the shipped container

## Phase Details

### Phase 1: One-Command Start

**Goal**: The user runs one command and gets a working app on port 8000 with a pre-seeded database that survives restarts
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DB-01, DB-02, DB-03, DB-04, SYS-01
**Success Criteria** (what must be TRUE):

  1. Running `scripts/start_mac.sh` (or the Windows PowerShell equivalent) builds and starts the single container, prints `http://localhost:8000`, and that URL serves the app on port 8000; running it twice is safe.
  2. On a fresh volume the backend creates the schema and seeds data with no manual step — a default profile with $10,000 cash and the ten default tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX).
  3. Stopping with the stop script and starting again keeps the same cash, positions and watchlist, because `db/finally.db` lives on the named volume mounted at `/app/db`.
  4. `GET /api/health` returns a healthy response, and the app reads `.env` from the project root with `.env.example` committed and `db/finally.db` gitignored.

**Plans:** 3 plans

Plans:
**Wave 1**

- [ ] 01-01-PLAN.md — Prove the container path end-to-end and add the HEALTHCHECK (DEP-01, DEP-02, DEP-05, DB-01..04, SYS-01)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-02-PLAN.md — Rewrite the mac start/stop scripts and prove the full lifecycle (DEP-03, DEP-02, DB-04)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md — Mirror the Windows scripts and document the database reset (DEP-04, DEP-05)

### Phase 2: Live Prices Streaming

**Goal**: The user opens the app and watches the default tickers tick live in a dark, data-dense terminal UI
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: MKT-01, MKT-02, MKT-03, MKT-04, MKT-05, MKT-06, MKT-07, MKT-08, STRM-01, STRM-02, STRM-03, UI-02, UI-03, UI-04, UI-12, UI-13, TEST-01
**Success Criteria** (what must be TRUE):

  1. The watchlist panel lists each default ticker with symbol, current price, daily change % and a sparkline, and prices refresh about twice a second with no page reload.
  2. A price cell flashes green on an uptick and red on a downtick, fading out over roughly half a second, driven by the direction carried in each stream event.
  3. Sparklines fill in progressively from the price updates accumulated since page load.
  4. With no `MASSIVE_API_KEY` the built-in simulator drives prices — realistic seed levels, correlated moves across related tickers, occasional 2-5% jolts — and with the key set the Massive REST poller drives them instead with nothing else in the app changing; both paths are covered by unit tests for the price math, response parsing and interface conformance.
  5. The app renders in the dark theme with the specified accent colors, fetches everything from same-origin `/api/*`, and resumes updates on its own after the stream connection drops.

**Plans**: TBD
**UI hint**: yes

### Phase 3: Watchlist Control & Ticker Detail

**Goal**: The user decides which tickers they watch and inspects any one of them in detail
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: WATCH-01, WATCH-02, WATCH-03, WATCH-04, UI-05, UI-11
**Success Criteria** (what must be TRUE):

  1. The user adds a ticker from the UI and it appears in the watchlist and starts streaming prices immediately, with no restart.
  2. The user removes a ticker and it disappears from the watchlist and from the price stream, and stays gone after a reload.
  3. `GET /api/watchlist` returns the watched tickers with their latest prices, matching what the panel shows.
  4. Clicking a ticker draws a larger price chart for it in the main chart area, and clicking a different ticker switches the chart to that one.

**Plans**: TBD
**UI hint**: yes

### Phase 4: Portfolio & Trading

**Goal**: The user trades the simulated $10,000 with market orders and sees the portfolio react everywhere
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, PORT-06, PORT-07, PORT-08, PORT-09, UI-01, UI-06, UI-07, UI-08, UI-09, TEST-02
**Success Criteria** (what must be TRUE):

  1. Buying from the trade bar fills instantly at the current price with no confirmation dialog and no fees: cash drops, and the position shows up in the positions table with ticker, quantity (fractional allowed), average cost, current price, unrealized P&L and % change.
  2. Selling fills instantly at the current price: cash rises, quantity drops, average cost stays correct, and a position that reaches zero disappears from the table.
  3. Buying beyond available cash or selling more shares than owned is rejected with a clear error and leaves cash and positions untouched, with trade math and edge cases pinned by unit tests.
  4. The header shows live total portfolio value, cash balance, and a connection dot that is green when connected, yellow when reconnecting and red when disconnected.
  5. The heatmap sizes each position by portfolio weight and colors it by P&L, and the P&L chart plots total portfolio value over time from snapshots recorded at seed and immediately after each trade.

**Plans**: TBD
**UI hint**: yes

### Phase 5: AI Trading Assistant

**Goal**: The user talks to FinAlly in natural language and it analyzes the portfolio and acts on it
**Mode:** mvp
**Depends on**: Phase 3, Phase 4
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07, CHAT-08, UI-10, TEST-03
**Success Criteria** (what must be TRUE):

  1. Sending a message in the collapsible chat panel shows a loading indicator and then one complete reply in the scrolling history.
  2. The reply reflects the user's real state — cash, positions with P&L, watchlist prices, total value — and earlier turns of the conversation, using structured output from the model.
  3. Asking the assistant to buy or sell executes the trade automatically through the same validation as a manual trade, confirmed inline in the chat; a trade that fails validation is explained in the reply instead of silently dropped.
  4. Asking the assistant to add or remove a ticker changes the watchlist right away, confirmed inline.
  5. The conversation and its executed actions survive a reload, `LLM_MOCK=true` returns deterministic replies without calling OpenRouter, and a malformed model response never breaks the request.

**Plans**: TBD
**UI hint**: yes

### Phase 6: Ship-Ready Verification

**Goal**: Anyone can clone the repo, run one command, and trust that the whole demo journey works
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):

  1. The Playwright suite runs with `LLM_MOCK=true` and passes: fresh start with streaming prices and $10k, watchlist add and remove, buy, sell, portfolio visuals with data, mocked chat that executes a trade, and stream reconnection.
  2. Backend route tests pass for every endpoint, covering status codes, response shapes and error paths.
  3. Browser-side unit tests pass, covering rendering with mock data, the price flash trigger, watchlist edits, portfolio calculations and chat loading states.
  4. A clean checkout plus the start script reaches a running app where the full suite passes from scratch.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. One-Command Start | 0/3 | Planned | - |
| 2. Live Prices Streaming | 0/TBD | Not started | - |
| 3. Watchlist Control & Ticker Detail | 0/TBD | Not started | - |
| 4. Portfolio & Trading | 0/TBD | Not started | - |
| 5. AI Trading Assistant | 0/TBD | Not started | - |
| 6. Ship-Ready Verification | 0/TBD | Not started | - |

---
*Roadmap created: 2026-09-20*
