<!-- refreshed: 2026-09-20 -->
# Architecture

**Analysis Date:** 2026-09-20

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                   Browser / Frontend (SPA)                        │
│              Next.js Static Export (React Components)             │
│    ├─ UI Components                                               │
│    ├─ EventSource SSE Client                                      │
│    └─ API Client                                                  │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTP + SSE
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              FastAPI Application (Python, port 8000)              │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ API Routers (`api/` module)                                 │  │
│  │ ├─ /api/health           Health check                       │  │
│  │ ├─ /api/portfolio        Portfolio state + positions        │  │
│  │ ├─ /api/portfolio/trade  Market order execution             │  │
│  │ ├─ /api/portfolio/history Portfolio value snapshots         │  │
│  │ ├─ /api/watchlist        Ticker watch list management       │  │
│  │ ├─ /api/stream/prices    SSE: live price updates            │  │
│  │ └─ /api/chat             LLM chat with auto-trades          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                       ▲                                             │
│                       │                                             │
│  ┌────────────────────┴──────────────────────────────────────────┐ │
│  │  Business Logic Layer                                          │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │ Portfolio Module (`portfolio/`)                          │ │ │
│  │  │ ├─ execute_trade() - validate & execute orders           │ │ │
│  │  │ ├─ build_portfolio_context() - aggregate positions       │ │ │
│  │  │ └─ TradeError exceptions                                 │ │ │
│  │  │                                                           │ │ │
│  │  │ LLM Module (`llm/`)                                       │ │ │
│  │  │ ├─ call_llm() - OpenRouter API via LiteLLM               │ │ │
│  │  │ ├─ build_messages() - system + context + history         │ │ │
│  │  │ ├─ mock_response() - deterministic testing               │ │ │
│  │  │ └─ ChatCompletion schema - structured output             │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                       ▲                                         │ │
│  │                       │                                         │ │
│  │  ┌────────────────────┴──────────────────────────────────────┐ │ │
│  │  │  Data Layer (Repository & Market)                         │ │ │
│  │  │                                                            │ │ │
│  │  │  Repository (`db/repository.py`)                          │ │ │
│  │  │  ├─ Sync function-based data access                      │ │ │
│  │  │  ├─ Cash balance                                         │ │ │
│  │  │  ├─ Positions & trades                                   │ │ │
│  │  │  ├─ Watchlist                                            │ │ │
│  │  │  ├─ Chat messages                                        │ │ │
│  │  │  └─ Portfolio snapshots                                  │ │ │
│  │  │                                                            │ │ │
│  │  │  Market Data (`market/`)                                  │ │ │
│  │  │  ├─ MarketDataProvider interface                         │ │ │
│  │  │  ├─ SimulatorProvider (GBM, correlated, events)          │ │ │
│  │  │  ├─ MassiveProvider (Polygon.io REST API polling)        │ │ │
│  │  │  ├─ PriceUpdate dataclass (immutable)                    │ │ │
│  │  │  └─ factory.make_provider() - env-driven selection       │ │ │
│  │  └────────────────────┬───────────────────────────────────┘ │ │
│  │                       │                                        │ │
│  └───────────────────────┴────────────────────────────────────────┘ │
│                          │                                           │
└──────────────────────────┼───────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌──────────┐   ┌─────────────┐   ┌─────────────┐
    │ SQLite   │   │  Market     │   │  OpenRouter │
    │ Database │   │  Data Feed  │   │  LLM API    │
    │ (local)  │   │  (Massive)  │   │             │
    └──────────┘   └─────────────┘   └─────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI App | Application entry point, lifespan management, router registration | `backend/main.py` |
| API Routers | HTTP endpoints, request/response handling | `backend/api/*.py` |
| Portfolio Module | Trade validation, execution, context aggregation | `backend/portfolio/trading.py`, `context.py` |
| LLM Module | OpenRouter integration, prompt building, response parsing | `backend/llm/client.py`, `prompt.py`, `schema.py` |
| Market Interface | Abstract provider contract | `backend/market/interface.py` |
| Market Simulator | In-process GBM price generator | `backend/market/simulator.py` |
| Market Massive | Polygon.io REST API client | `backend/market/massive.py` |
| Repository | SQLite data access functions | `backend/db/repository.py` |
| Schema | Database DDL | `backend/db/schema.py` |
| Next.js SPA | Browser UI, component tree, state management | `frontend/src/` |
| usePrice Stream Hook | SSE connection & price history accumulation | `frontend/src/lib/usePriceStream.ts` |
| API Client | Fetch wrapper for all backend endpoints | `frontend/src/lib/api.ts` |

## Pattern Overview

**Overall:** Layered monolith with a clean separation of concerns: API routes → business logic → data access. Market data abstraction decouples price source. SSE for one-way server-push. Structured outputs from LLM enable auto-execution.

**Key Characteristics:**
- **Single Docker container**: Frontend static export served by FastAPI; no CORS, one port, simple deployment
- **Market data abstraction**: Two implementations (simulator and Massive) behind a common interface; provider selected at startup via environment variable
- **Repository pattern**: Plain functions (no ORM) for data access; each write opens connection and commits
- **Lazy DB initialization**: Tables created on first access; seed data populates automatically
- **SSE streaming**: Server-side event stream pushes all known prices on a regular cadence; client accumulates history for sparklines
- **Structured LLM output**: JSON response schema validated at parse time; trades and watchlist changes auto-execute
- **Lifespan context manager**: FastAPI's `@asynccontextmanager` manages market provider startup/shutdown

## Layers

**Presentation Layer (Frontend):**
- Purpose: React SPA running in the browser; renders all UI, manages user interactions, accumulates price history
- Location: `frontend/src/`
- Contains: Components, hooks, API client, type definitions, utilities
- Depends on: Backend API routes (`/api/*`) and SSE stream (`/api/stream/*`)
- Used by: End user in browser

**API/Route Layer:**
- Purpose: FastAPI routers; HTTP request → validation → delegation to business logic
- Location: `backend/api/`
- Contains: Health, portfolio, trade, watchlist, stream, chat routers
- Depends on: Portfolio & LLM business logic, repository, market provider
- Used by: Frontend (HTTP/SSE client)

**Business Logic Layer:**
- Purpose: Trade validation, portfolio context aggregation, LLM integration
- Location: `backend/portfolio/`, `backend/llm/`
- Contains: Trade execution logic, portfolio context builder, LLM prompt construction, mock responses
- Depends on: Repository, market provider, OpenRouter API
- Used by: API routes, tests

**Data Access Layer:**
- Purpose: SQLite operations; isolation of SQL from business logic
- Location: `backend/db/repository.py`
- Contains: Pure functions for CRUD operations on all tables
- Depends on: SQLite connection
- Used by: Business logic, API routes

**Market Data Layer:**
- Purpose: Abstraction of price sources; provides current prices and manages background update task
- Location: `backend/market/`
- Contains: MarketDataProvider interface, SimulatorProvider, MassiveProvider, factory
- Depends on: Nothing (self-contained); optionally calls Massive API
- Used by: API stream route, portfolio context builder, trade executor

## Data Flow

### Primary Request Path (Manual Trade)

1. Frontend sends POST `/api/portfolio/trade` with ticker, quantity, side
   - Request handler in `backend/api/portfolio.py:post_trade()`
2. Handler retrieves current prices from market provider (`request.app.state.provider.get_prices()`)
3. Calls `backend/portfolio/trading.py:execute_trade()` with ticker, side, quantity, prices
4. Trade execution validates:
   - Ticker has a live price available
   - Side is valid ("buy" or "sell")
   - Quantity is positive
   - For buy: sufficient cash available
   - For sell: sufficient shares owned
5. If valid:
   - Update position (insert or update) via `repository.upsert_position()`
   - Update cash balance via `repository.set_cash_balance()`
   - Record trade in trade history via `repository.record_trade()`
6. Rebuild portfolio context (aggregate positions, calculate P&L, total value)
7. Record portfolio snapshot via `repository.record_snapshot()`
8. Return updated portfolio context (JSON) to frontend
9. Frontend re-polls `/api/portfolio` on response receipt to sync UI

### SSE Stream Path (Live Prices)

1. Frontend opens EventSource connection to `/api/stream/prices`
2. Backend route `backend/api/stream.py:stream_prices()` initializes async generator
3. Background market provider (simulator or Massive) maintains current price cache
4. Stream generator loops:
   - Retrieve latest prices from provider (`provider.get_prices()`)
   - Serialize each PriceUpdate to JSON
   - Yield SSE event (`data: {...}\n\n`)
   - Sleep 0.5s (TICK_SECONDS)
5. Frontend EventSource receives events, parses JSON, accumulates price history per ticker
6. Components read from price history to render sparklines and flash animations

### Chat with LLM Path (Auto-Execution)

1. Frontend sends POST `/api/chat` with user message
2. Handler in `backend/api/chat.py:chat()` loads:
   - Recent chat history (last 20 messages) from `repository.list_recent_chat_messages()`
   - Current portfolio context (positions, cash, P&L) from `build_portfolio_context()`
   - Current prices from market provider
3. Checks if `LLM_MOCK=true`:
   - If yes: call `llm.mock.mock_response()` for deterministic test response
   - If no: call `llm.client.call_llm()` via OpenRouter with structured output schema
4. LLM response parsed into `ChatCompletion` (message, trades[], watchlist_changes[])
5. Auto-execute trades:
   - For each trade in response: call `execute_trade()` with current prices
   - Catch `TradeError` for validation failures; include error in results
6. Apply watchlist changes:
   - Add/remove tickers from watchlist via `repository.add_watchlist_ticker()` / `remove_watchlist_ticker()`
   - Update market provider's tracked ticker set if any change succeeds
7. Store both messages:
   - User message via `repository.add_chat_message("user", message_text)`
   - Assistant message via `repository.add_chat_message("assistant", completion.message, action_summary=summary)`
8. Return complete response (message, trade results, watchlist results) to frontend

**State Management:**
- Backend: Synchronous, single-threaded SQLite; no intermediate cache; all state lives in database
- Frontend: React component state; price history in `usePriceStream` hook; portfolio/watchlist state in page component; synced via API polling (4s for portfolio, 10s for history)
- Market data: In-memory cache in provider instance; GBM state in simulator; persists only for the lifetime of the provider task

## Key Abstractions

**MarketDataProvider:**
- Purpose: Abstract price source; enables swapping simulator ↔ Massive without changing downstream code
- Examples: `backend/market/simulator.py:SimulatorProvider`, `backend/market/massive.py:MassiveProvider`
- Pattern: ABC with abstract methods; concrete implementations override `start()`, `stop()`, `get_prices()`, `update_tickers()`
- Ensures: Consistent interface for price queries and background task management

**PriceUpdate:**
- Purpose: Immutable data class representing a single price observation
- Examples: Yielded by simulator tick; returned by provider.get_prices()
- Pattern: Frozen dataclass (hashable, thread-safe conceptually though not needed here)
- Fields: ticker, price, prev_price, change_pct, timestamp

**ChatCompletion:**
- Purpose: Structured output from LLM; validated at parse time
- Examples: `backend/llm/schema.py:ChatCompletion`
- Pattern: Pydantic BaseModel with nested ChatTrade and WatchlistChange models
- Ensures: Type-safe access to message, trades, and watchlist_changes; failures during parsing caught early

**TradeError:**
- Purpose: User-facing trade validation exception
- Examples: "Insufficient cash", "Invalid side", "No live price"
- Pattern: Custom exception with message safe to return in HTTP 400 response
- Ensures: Graceful error reporting; trade never executes partially on validation failure

## Entry Points

**Browser Entry Point:**
- Location: `/` (root path)
- Triggers: User navigates to `http://localhost:8000`
- Responsibilities: FastAPI serves static `index.html` from frontend build; browser loads SPA; hooks initialize (price stream, initial data load)

**API Health Check:**
- Location: `backend/api/health.py:get_health()`
- Triggers: GET `/api/health`
- Responsibilities: Returns `{"status": "ok", "market_provider": "simulator" | "massive"}`; used by Docker for liveness probes

**Portfolio Query:**
- Location: `backend/api/portfolio.py:get_portfolio()`
- Triggers: GET `/api/portfolio`
- Responsibilities: Aggregates current positions, cash, total value, P&L from repository and prices

**Trade Execution:**
- Location: `backend/api/portfolio.py:post_trade()`
- Triggers: POST `/api/portfolio/trade` with TradeRequest (ticker, quantity, side)
- Responsibilities: Validates, executes, records, snapshots, returns updated context

**Portfolio History:**
- Location: `backend/api/portfolio.py:get_history()`
- Triggers: GET `/api/portfolio/history`
- Responsibilities: Returns array of portfolio snapshots for P&L chart

**Watchlist Query/Modify:**
- Location: `backend/api/watchlist.py:*`
- Triggers: GET/POST/DELETE `/api/watchlist[/{ticker}]`
- Responsibilities: List, add, remove tickers; update market provider on change

**SSE Price Stream:**
- Location: `backend/api/stream.py:stream_prices()`
- Triggers: GET `/api/stream/prices` (opens EventSource connection)
- Responsibilities: Yields price updates every 0.5s; server keeps connection open until client disconnects

**Chat:**
- Location: `backend/api/chat.py:chat()`
- Triggers: POST `/api/chat` with ChatRequest (message)
- Responsibilities: Loads context, calls LLM, executes trades/watchlist changes, stores history, returns response

## Architectural Constraints

- **Threading:** Single-threaded event loop (asyncio) in backend. Simulator and Massive both run background asyncio tasks. SQLite (WAL mode) is thread-safe but this codebase has no explicit threading — all I/O via asyncio.
- **Global state:** One market provider instance stored in `app.state.provider` (FastAPI lifespan). No other singletons. SSE generator is stateless (reads from provider cache on each tick).
- **Circular imports:** Market factory imports provider interface and implementations; providers don't import factory. Repository and schema have no dependencies on business logic layers. No known circular dependencies.
- **Database connection:** Single SQLite file at runtime path `/app/db/finally.db` (mounted volume in Docker). No connection pool; `get_connection()` returns same thread-local or global connection. No explicit transaction wrapping; each function commits after write.
- **SSE client reconnection:** EventSource handles automatic retry (exponential backoff). No state preserved across reconnects on frontend; price history is reset (accumulation restarts).
- **LLM latency:** LLM calls are synchronous (await). Cerebras inference is fast (~few seconds); UI shows loading spinner. No token-streaming.

## Anti-Patterns

### Hard-Coded Default User

**What happens:** All queries assume a single user with ID = 1 (or implicitly a "default" user). No `user_id` column in tables; no multi-user support at the data layer despite planning for it.

**Why it's wrong:** Future multi-user feature (mentioned in PLAN.md §7) would require schema migration and backfilling. Any user data is globally visible; no tenant isolation.

**Do this instead:** For single-user scope phase, this is acceptable. Document it explicitly in schema and repository. When multi-user is planned, add `user_id` column to all tables at once (schema migration step) and wrap repository functions with a user context parameter.

### Trade Execution Without Atomicity

**What happens:** `execute_trade()` performs multiple writes (position, cash, trade record, snapshot) via separate function calls to repository. If one write fails, prior writes are not rolled back.

**Why it's wrong:** Portfolio inconsistency. E.g., position updated but cash not decremented; or cash decremented but trade not recorded.

**Do this instead:** Wrap all writes in a SQLite transaction. Refactor repository functions to accept an optional connection parameter so caller can manage BEGIN/COMMIT. Or use a context manager pattern:
```python
with transaction():
    repository.upsert_position(...)
    repository.set_cash_balance(...)
    repository.record_trade(...)
```

### Unbounded Price History on Frontend

**What happens:** `usePriceStream` accumulates price ticks indefinitely (capped at 240 per ticker). On long-lived page sessions, memory grows; chart rendering may slow.

**Why it's wrong:** Memory leak; performance degrades after hours of price updates.

**Do this instead:** Implement a time-window accumulation (last 1 hour of ticks) rather than a count-based limit. Or paginate history: chartable ticks on frontend, full history keyed in backend for export.

### No Validation of Watchlist Ticker Format

**What happens:** User (or LLM) can add any string as a ticker via `/api/watchlist` POST. No check that it's a valid symbol (uppercase, alphanumeric, 1-5 chars, etc.).

**Why it's wrong:** Watchlist contains garbage; market provider may crash or return no data for non-existent tickers; SSE includes invalid tickers.

**Do this instead:** Validate ticker format in `add_watchlist_ticker()`. Optionally, query market provider to confirm price is available before adding. Reject with HTTP 400 if invalid.

### Chat Auto-Execution Proceeds After LLM Parse Failure

**What happens:** If LLM response is malformed JSON, `call_llm()` raises `ValueError`. Chat handler catches and returns a fallback message. But then `_apply_trades()` and `_apply_watchlist_changes()` are called with empty arrays, which silently succeeds (no trades attempted).

**Why it's wrong:** Subtle logic: if LLM intends trades but response is malformed, user is not informed that trades did not execute. Messages appear in history suggesting actions happened.

**Do this instead:** On LLM parse failure, return early without storing chat message. Or, store a flag indicating the response was partial/failed and reflect that to the user.

---

*Architecture analysis: 2026-09-20*
