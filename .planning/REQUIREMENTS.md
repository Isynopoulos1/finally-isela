# Requirements: FinAlly

**Defined:** 2026-09-20
**Core Value:** The user watches prices stream live, trades a simulated portfolio, and tells the AI assistant in natural language to analyze or trade it — all in one dense, dark terminal UI that starts with a single command.

## v1 Requirements

Every capability in `planning/PLAN.md`. Existing code is reused where it satisfies a requirement; each phase verifies it.

### Market Data

- [ ] **MKT-01**: Simulator generates ticker prices with geometric Brownian motion using per-ticker drift and volatility, updating about every 500ms
- [ ] **MKT-02**: Simulator produces correlated moves across related tickers (e.g. tech stocks)
- [ ] **MKT-03**: Simulator occasionally applies a sudden 2-5% move to a single ticker
- [ ] **MKT-04**: Simulator starts each default ticker from a realistic seed price
- [ ] **MKT-05**: When `MASSIVE_API_KEY` is set, the backend polls the Massive REST API for the union of watched tickers on a configurable interval
- [ ] **MKT-06**: When `MASSIVE_API_KEY` is absent or empty, the backend uses the built-in simulator
- [ ] **MKT-07**: Simulator and Massive client implement the same interface, so downstream code is source-agnostic
- [ ] **MKT-08**: A single background task writes latest price, previous price and timestamp per ticker to a shared in-memory cache

### Streaming

- [ ] **STRM-01**: `GET /api/stream/prices` is a long-lived SSE stream pushing updates for all watched tickers about every 500ms
- [ ] **STRM-02**: Each SSE event carries ticker, price, previous price, timestamp and change direction
- [ ] **STRM-03**: The browser client reconnects automatically after a dropped connection

### Database

- [ ] **DB-01**: On first start (file missing, empty or tables absent) the backend creates the schema and seeds data with no manual step
- [ ] **DB-02**: Seed data is one default profile with $10,000 cash and a watchlist of AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX
- [ ] **DB-03**: SQLite holds `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots` and `chat_messages` as specified in PLAN.md §7
- [ ] **DB-04**: The database file `db/finally.db` persists across container restarts

### Portfolio and Trading

- [ ] **PORT-01**: `GET /api/portfolio` returns positions, cash balance, total value and unrealized P&L
- [ ] **PORT-02**: User can buy shares with a market order that fills instantly at the current price, with no fees
- [ ] **PORT-03**: User can sell shares with a market order that fills instantly at the current price
- [ ] **PORT-04**: Trades support fractional quantities
- [ ] **PORT-05**: A buy exceeding available cash is rejected with a clear error
- [ ] **PORT-06**: A sell exceeding shares owned is rejected with a clear error
- [ ] **PORT-07**: Average cost updates correctly on buys, and a position is removed when its quantity reaches zero
- [ ] **PORT-08**: A portfolio snapshot is recorded every 30 seconds and immediately after each trade
- [ ] **PORT-09**: `GET /api/portfolio/history` returns the snapshots for the P&L chart

### Watchlist

- [ ] **WATCH-01**: `GET /api/watchlist` returns watched tickers with their latest prices
- [ ] **WATCH-02**: User can add a ticker via `POST /api/watchlist`
- [ ] **WATCH-03**: User can remove a ticker via `DELETE /api/watchlist/{ticker}`
- [ ] **WATCH-04**: A newly added ticker starts streaming prices without a restart

### AI Chat

- [ ] **CHAT-01**: `POST /api/chat` returns one complete JSON response containing the message and any executed actions
- [ ] **CHAT-02**: The prompt includes cash, positions with P&L, watchlist with live prices, total value, and recent conversation history
- [ ] **CHAT-03**: The LLM is called via LiteLLM → OpenRouter with Cerebras inference and returns structured output matching the schema (`message`, `trades`, `watchlist_changes` with add and remove)
- [ ] **CHAT-04**: Trades from the LLM execute automatically through the same validation as manual trades, and failures are reported in the chat response
- [ ] **CHAT-05**: Watchlist changes from the LLM execute automatically
- [ ] **CHAT-06**: Each user message and assistant reply, with its executed actions, is stored in `chat_messages`
- [ ] **CHAT-07**: With `LLM_MOCK=true` the backend returns deterministic responses without calling OpenRouter
- [ ] **CHAT-08**: A malformed LLM response is handled without crashing the request

### System

- [ ] **SYS-01**: `GET /api/health` returns a health check response

### Frontend

- [ ] **UI-01**: Header shows live total portfolio value, cash balance, and a connection dot (green connected, yellow reconnecting, red disconnected)
- [ ] **UI-02**: Watchlist panel shows ticker, current price, daily change % and a sparkline for each ticker
- [ ] **UI-03**: Price cells flash green on an uptick and red on a downtick, fading over about 500ms
- [ ] **UI-04**: Sparklines fill progressively from SSE data accumulated since page load
- [ ] **UI-05**: Clicking a ticker shows a larger price chart for it in the main chart area
- [ ] **UI-06**: Portfolio heatmap (treemap) sizes each position by weight and colors it by P&L
- [ ] **UI-07**: P&L line chart shows total portfolio value over time from snapshots
- [ ] **UI-08**: Positions table shows ticker, quantity, average cost, current price, unrealized P&L and % change
- [ ] **UI-09**: Trade bar has ticker and quantity fields with buy and sell buttons and no confirmation dialog
- [ ] **UI-10**: Chat panel is collapsible, with message input, scrolling history, a loading indicator, and inline trade and watchlist confirmations
- [ ] **UI-11**: User can add and remove watchlist tickers from the UI
- [ ] **UI-12**: Dark theme with the specified accent colors, desktop-first and functional on tablet
- [ ] **UI-13**: All frontend API calls go to the same origin (`/api/*`)

### Deployment

- [ ] **DEP-01**: A multi-stage Dockerfile (Node build, then Python 3.12 with uv) produces one image serving API and static frontend on port 8000
- [ ] **DEP-02**: The container persists the database through a named Docker volume mounted at `/app/db`
- [ ] **DEP-03**: `scripts/start_mac.sh` and `stop_mac.sh` build and run or stop the container idempotently, print the URL, and keep the volume on stop
- [ ] **DEP-04**: `scripts/start_windows.ps1` and `stop_windows.ps1` provide the same behavior on Windows
- [ ] **DEP-05**: `.env` is read at the project root, `.env.example` is committed, and `db/finally.db` is gitignored

### Testing

- [ ] **TEST-01**: Backend unit tests cover simulator price validity, GBM math, Massive response parsing and interface conformance
- [ ] **TEST-02**: Backend unit tests cover trade execution, P&L math and edge cases (oversell, insufficient cash, sell at a loss)
- [ ] **TEST-03**: Backend unit tests cover structured-output parsing, malformed responses and trade validation in the chat flow
- [ ] **TEST-04**: Backend unit tests cover API route status codes, response shapes and errors
- [ ] **TEST-05**: Frontend unit tests cover component rendering, price flash, watchlist CRUD, portfolio calculations and chat rendering with loading state
- [ ] **TEST-06**: Playwright E2E tests with `LLM_MOCK=true` cover fresh start, watchlist add/remove, buy, sell, heatmap and P&L chart, mocked chat with inline trade, and SSE reconnection

## v2 Requirements

Deferred. Tracked but not in the current roadmap.

### Extensions

- **EXT-01**: Price history endpoint so sparklines and the main chart survive a page refresh
- **EXT-02**: Terraform configuration for AWS App Runner deployment
- **EXT-03**: Multi-user support with authentication

## Out of Scope

| Feature | Reason |
|---------|--------|
| Limit orders, partial fills, order book | Market orders only keeps portfolio math simple |
| Authentication and multi-user | Single hardcoded user; `user_id` columns are only a future hook |
| Token-by-token LLM streaming | Cerebras is fast enough for a loading indicator |
| WebSocket transport | SSE covers one-way push |
| Cloud deployment (core build) | Stretch goal only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|

**Coverage:**
- v1 requirements: 61 total
- Mapped to phases: 0
- Unmapped: 61 ⚠️

---
*Requirements defined: 2026-09-20*
*Last updated: 2026-09-20 after initial definition*
