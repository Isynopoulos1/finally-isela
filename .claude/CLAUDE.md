<!-- GSD:project-start source:PROJECT.md -->

## Project

**FinAlly — Finance Ally**

An AI-powered trading workstation with a Bloomberg-terminal look: it streams live market data, lets the user trade a simulated $10,000 portfolio, and includes an LLM chat assistant that can analyze positions and execute trades and watchlist changes on the user's behalf. It is the capstone project for an agentic AI coding course, run as a single Docker container on port 8000 with no login. The full specification lives in `planning/PLAN.md`.

**Core Value:** The user watches prices stream live, trades a simulated portfolio, and tells the AI assistant in natural language to analyze or trade it — all in one dense, dark terminal UI that starts with a single command.

### Constraints

- **Architecture**: Single container, single port (8000), FastAPI serving the Next.js static export — keeps deployment to one command
- **Tech stack**: Python/FastAPI managed with `uv`; Next.js + TypeScript + Tailwind; SQLite; SSE — per PLAN.md
- **Code style**: Simple, incremental, no over-engineering or defensive programming; short modules and functions; latest library APIs; concise docstrings
- **Debugging**: Identify and prove the root cause before fixing
- **Visual**: Dark theme (`#0d1117`/`#1a1a2e`), accent yellow `#ecad0a`, blue `#209dd7`, purple `#753991` for submit buttons; desktop-first

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- TypeScript 5.x - Frontend application (`frontend/`)
- Python 3.12 - Backend server and all server logic (`backend/`)
- JavaScript (Vite configuration and tooling)

## Runtime

- Node.js 24-slim (Docker build stage for frontend)
- Python 3.12-slim (Docker runtime for backend)
- npm (frontend) - lockfile present: `frontend/package-lock.json`
- uv (backend) - modern Python project manager - lockfile present: `backend/uv.lock`

## Frameworks

- Next.js 16.3.5 - Full-stack React framework, configured for static export (`output: "export"` in `frontend/next.config.ts`)
- React 19.2.8 - UI library
- TypeScript 5.x - Type safety
- FastAPI 0.141.1+ - Async web framework for REST API and SSE streaming
- Uvicorn 0.53.0+ - ASGI server running on port 8000
- Pydantic 2.13.5+ - Data validation and settings management
- Vitest 5.0.1 - Frontend unit/integration tests with jsdom environment
- pytest 8.0+ - Backend unit tests
- pytest-asyncio 0.24+ - Async test support for FastAPI routes
- Playwright 1.63.0 - E2E browser automation tests
- Next.js build system (Turbopack for dev, static export for prod)
- uv for Python dependency lockfile management
- Ruff 0.6+ - Python linter/formatter
- Tailwind CSS 4.x - Utility-first CSS framework
- PostCSS 4.x - CSS transformation via `@tailwindcss/postcss` plugin
- Tailwind CSS TypeScript types via `@tailwindcss/postcss`

## Key Dependencies

- `lightweight-charts` 5.2.1 - Canvas-based charting library for real-time price charts and sparklines
- `react-dom` 19.2.8 - React rendering for browser DOM
- `@vitejs/plugin-react` 6.1.1 - Vite + React support for test environment
- `@testing-library/react` 16.3.3 - React component testing utilities
- `@testing-library/jest-dom` 7.0.1 - Jest matchers for DOM assertions
- `@testing-library/user-event` 14.6.7 - User interaction simulation
- `jsdom` 30.1.0 - Simulated DOM for unit tests
- `@types/react` 19.x - React type definitions
- `@types/react-dom` 19.x - React DOM type definitions
- `@types/node` 26.x - Node.js type definitions (Next.js requirement)
- `eslint` 9.x - JavaScript/TypeScript linting via flat config
- `eslint-config-next` 16.3.5 - Next.js ESLint rules (core web vitals + TypeScript)
- `fastapi` - Async web framework for `/api/*` routes and SSE streaming at `GET /api/stream/prices`
- `httpx` 0.27+ - Async HTTP client for Massive API calls
- `litellm` 1.101.0+ - Unified LLM interface to OpenRouter API
- `openai` 2.54.0+ - OpenAI SDK for structured outputs (used by LiteLLM for Pydantic validation)
- `pydantic` 2.13.5+ - Data validation for request/response schemas and LLM structured output parsing
- `python-dotenv` 1.2.3+ - Load environment variables from `.env` file
- `uvicorn[standard]` 0.53.0+ - ASGI server with full feature set
- `pytest` 8.0+ - Test framework
- `pytest-asyncio` 0.24+ - Async test support
- `ruff` 0.6+ - Fast Python linter/formatter
- `httpx2` 2.13.0+ - Testing utilities (likely for mocking HTTP)

## Configuration

- `.env` file (git-ignored, `.env.example` provided) contains:
- `python-dotenv` loads `.env` in backend at `backend/llm/client.py`
- `frontend/tsconfig.json` - TypeScript configuration with strict mode, path aliases (`@/*` → `./src/*`)
- `frontend/next.config.ts - Static export configuration (`output: "export"`, unoptimized images)
- `frontend/vitest.config.mts` - Vitest configuration: jsdom environment, React plugin, setup file at `vitest.setup.ts`
- `frontend/eslint.config.mjs` - Flat ESLint config: Next.js web vitals + TypeScript, ignores `.next/`, `out/`, `build/`
- `frontend/postcss.config.mjs` - PostCSS configured with Tailwind CSS plugin
- `backend/pyproject.toml` - uv project manifest with dependencies, dev tools, test config
- `backend/llm/client.py` - Hardcoded: `MODEL = "openrouter/openai/gpt-oss-120b"`, `EXTRA_BODY = {"provider": {"order": ["cerebras"]}}`

## Platform Requirements

- Node.js 24.x (for frontend `npm install` and `next dev`)
- Python 3.12.x (for backend `uv sync` and test runs)
- SQLite 3 (bundled in Python standard library and via Docker)
- Docker (single container image, multi-stage: Node → Python)
- Docker volume mount at `/app/db` for SQLite persistence
- Port 8000 exposed (FastAPI server)
- Environment variables injected via `--env-file .env` or Docker secrets

## Docker Build

- **Stage 1 (frontend-build):** `node:24-slim` → builds Next.js static export to `frontend/out/`
- **Stage 2 (backend/runtime):** `python:3.12-slim` → installs uv, syncs Python deps, copies frontend static files into `backend/static/`, runs FastAPI on port 8000
- **Multi-stage result:** Single image with Next.js build output and FastAPI server

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

### TypeScript/Frontend Files

- Components: PascalCase (e.g., `Watchlist.tsx`, `TradeBar.tsx`, `WatchlistRow.tsx`)
- Utilities/Hooks: camelCase (e.g., `usePriceStream.ts`, `api.ts`, `types.ts`, `format.ts`)
- Test files: Match source file name with `.test.tsx` suffix (e.g., `Watchlist.test.tsx`)
- Directories: kebab-case for feature directories, `__tests__` for test colocations
- React components: PascalCase, exported as named exports (e.g., `export function Watchlist(...)`)
- Custom hooks: `use` prefix + PascalCase (e.g., `usePriceStream()`)
- Event handlers: `handle` + event name in camelCase (e.g., `handleAdd`, `handleSelect`)
- Regular functions: camelCase (e.g., `waitForLivePrice()`)
- API methods: camelCase, object-organized (e.g., `api.getWatchlist()`, `api.addTicker()`)
- State variables: camelCase (e.g., `ticker`, `quantity`, `pending`, `priceHistory`)
- Type/interface variable names: PascalCase (e.g., `WatchlistItem`, `Position`)
- Constants: camelCase or UPPER_SNAKE_CASE depending on context
- Use `interface` keyword (not `type`) for object shapes (e.g., `interface WatchlistProps { ... }`)
- Use `type` for unions and literals (e.g., `type TradeSide = "buy" | "sell"`)
- Import types with `import type { ... }` for tree-shaking
- Suffix component prop interfaces with `Props` (e.g., `WatchlistProps`, `TradeBarProps`)

### Python/Backend Files

- Modules: snake_case (e.g., `simulator.py`, `schema.py`, `trading.py`)
- Package directories: snake_case (e.g., `market/`, `portfolio/`, `api/`, `db/`, `llm/`)
- Test files: `test_` prefix + module name (e.g., `test_market_simulator.py`, `test_db_schema.py`)
- Functions: snake_case (e.g., `execute_trade()`, `build_portfolio_context()`, `normalize()`)
- Private functions: `_` prefix (e.g., `_table_names()`, `_correlation()`)
- Async functions: same snake_case convention (e.g., `async def start()`)
- Classes: PascalCase (e.g., `TradeError`, `ChatCompletion`, `SimulatorProvider`)
- Exception classes: Inherit from `Exception` with `Error` suffix (e.g., `class TradeError(Exception)`)
- Pydantic models: PascalCase (e.g., `ChatCompletion`, `ChatTrade`, `WatchlistChange`)
- Function/module-level: snake_case (e.g., `ticker`, `quantity`, `cash_balance`)
- Constants: UPPER_SNAKE_CASE (e.g., `MIN_QUANTITY = 1e-9`, `ANNUAL_VOL`)
- Logger: `log = logging.getLogger(__name__)`

## Code Style

### Formatting

- No `.prettierrc` configured; relies on ESLint for style enforcement
- ESLint config: `eslint.config.mjs` (flat config format, ESLint v9+)
- Extends: `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`
- Indentation: 2 spaces (inferred from codebase)
- Line length: Implied ~80-100 characters (no explicit config)
- Semicolons: Required (ESLint default)
- Ruff for linting and formatting
- Configuration in `pyproject.toml`:

### Linting

- Tool: ESLint 9 (flat config)
- Config file: `frontend/eslint.config.mjs`
- Enforces Next.js best practices, TypeScript strict mode
- Ignores: `.next/`, `out/`, `build/`, `next-env.d.ts`
- Tool: Ruff
- Config in `backend/pyproject.toml`
- Manages both style and linting together

## Import Organization

### Frontend

- `@/*` → `./src/*` (configured in `tsconfig.json`)
- All internal imports use `@/` for clarity and IDE support

### Backend

## Error Handling

### Frontend

- Catch all errors as `catch (err)` or `catch (err instanceof Error ? err.message : "...")`
- Display user-friendly error messages in state (e.g., `error` state rendered as `<p className="text-down">{error}</p>`)
- Clear errors on successful operations (`setError(null)`)
- For network errors, show the fetch error message directly or a generic fallback

### Backend

- Define domain-specific exception classes (e.g., `TradeError`) that inherit from `Exception`
- Include docstring explaining when the error is raised
- Catch and convert to HTTP responses in API routes:
- Messages in `TradeError` are designed to be safe to show to users
- Use `raise ... from exc` for exception chaining to preserve tracebacks
- Pydantic models handle request validation automatically via `BaseModel`
- Invalid side, quantity, or missing fields raise `ValidationError` → 422 response automatically

## Logging

### Frontend

- Minimal console output; use in development only via conditional logging
- No structured logging library used
- Most state is tracked via React state, not logs

### Backend

- Each module creates a logger: `log = logging.getLogger(__name__)`
- Used in market data providers (`market/simulator.py`, `market/massive.py`, `market/factory.py`)
- Log messages for informational events (e.g., provider startup/shutdown)
- No structured logging format configured; uses default format

## Comments

### When to Comment

- **Module docstrings:** Required for all `.py` files. Explain module purpose.
- **Function docstrings:** Optional but recommended for complex logic.
- **Inline comments:** Rare. Only for non-obvious logic or important invariants.

### JSDoc/TSDoc

- **Not used** in this codebase. TypeScript interfaces and type annotations are sufficient.
- Function signatures are clear enough that docstrings are rarely needed.

## Function Design

### Size

- React components: 20-100 lines typical. Extracted smaller pieces as separate components if logic grows.
- Custom hooks: 20-40 lines. State and side effects clearly isolated.
- Utility functions: Short, single-purpose (e.g., `request<T>(...)` for API calls, ~20 lines)
- Functions: 10-50 lines typical. Multi-step processes broken into smaller functions.
- Example: `execute_trade()` is ~50 lines covering buy/sell branches

### Parameters

- React components: Props passed as a destructured object (`{ items, priceHistory, selectedTicker, ... }`)
- Functions: Use object params for 3+ arguments (e.g., API request options)
- Functions: Named parameters with type hints
- Avoid excessive parameter nesting; use Pydantic models for complex inputs

### Return Values

- React components: Return JSX (no explicit return type in function signature, let TypeScript infer)
- Functions: Use explicit return types
- Functions: Include return type in signature
- Async functions: Return type is wrapped in coroutine, but signature shows unwrapped type

## Module Design

### Exports

- Named exports preferred (`export function Watchlist(...) { }`)
- Default exports avoided (helps with tree-shaking and clarity)
- Index files (`index.ts`) used rarely; direct imports preferred
- Functions and classes exported at module level for import
- `__init__.py` files minimal (often empty)
- Public API exposed via `from module import function`

### Barrel Files

- Not used. Each component imported directly from its file.
- Not used in this codebase. Direct imports from modules.

## TypeScript Configuration

- `"strict": true` — Strict type checking enabled
- `"jsx": "react-jsx"` — JSX handled by React 18+ transform
- `"moduleResolution": "bundler"` — Next.js bundler resolution
- `"skipLibCheck": true` — Skip checking .d.ts files for performance
- `"resolveJsonModule": true` — JSON imports allowed
- Path aliases: `"@/*": ["./src/*"]`
- All values must be typed
- `null` and `undefined` are distinct (no implicit union)
- Function parameters must have types
- Improves IDE support and catches bugs at compile time

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

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

- **Single Docker container**: Frontend static export served by FastAPI; no CORS, one port, simple deployment
- **Market data abstraction**: Two implementations (simulator and Massive) behind a common interface; provider selected at startup via environment variable
- **Repository pattern**: Plain functions (no ORM) for data access; each write opens connection and commits
- **Lazy DB initialization**: Tables created on first access; seed data populates automatically
- **SSE streaming**: Server-side event stream pushes all known prices on a regular cadence; client accumulates history for sparklines
- **Structured LLM output**: JSON response schema validated at parse time; trades and watchlist changes auto-execute
- **Lifespan context manager**: FastAPI's `@asynccontextmanager` manages market provider startup/shutdown

## Layers

- Purpose: React SPA running in the browser; renders all UI, manages user interactions, accumulates price history
- Location: `frontend/src/`
- Contains: Components, hooks, API client, type definitions, utilities
- Depends on: Backend API routes (`/api/*`) and SSE stream (`/api/stream/*`)
- Used by: End user in browser
- Purpose: FastAPI routers; HTTP request → validation → delegation to business logic
- Location: `backend/api/`
- Contains: Health, portfolio, trade, watchlist, stream, chat routers
- Depends on: Portfolio & LLM business logic, repository, market provider
- Used by: Frontend (HTTP/SSE client)
- Purpose: Trade validation, portfolio context aggregation, LLM integration
- Location: `backend/portfolio/`, `backend/llm/`
- Contains: Trade execution logic, portfolio context builder, LLM prompt construction, mock responses
- Depends on: Repository, market provider, OpenRouter API
- Used by: API routes, tests
- Purpose: SQLite operations; isolation of SQL from business logic
- Location: `backend/db/repository.py`
- Contains: Pure functions for CRUD operations on all tables
- Depends on: SQLite connection
- Used by: Business logic, API routes
- Purpose: Abstraction of price sources; provides current prices and manages background update task
- Location: `backend/market/`
- Contains: MarketDataProvider interface, SimulatorProvider, MassiveProvider, factory
- Depends on: Nothing (self-contained); optionally calls Massive API
- Used by: API stream route, portfolio context builder, trade executor

## Data Flow

### Primary Request Path (Manual Trade)

### SSE Stream Path (Live Prices)

### Chat with LLM Path (Auto-Execution)

- Backend: Synchronous, single-threaded SQLite; no intermediate cache; all state lives in database
- Frontend: React component state; price history in `usePriceStream` hook; portfolio/watchlist state in page component; synced via API polling (4s for portfolio, 10s for history)
- Market data: In-memory cache in provider instance; GBM state in simulator; persists only for the lifetime of the provider task

## Key Abstractions

- Purpose: Abstract price source; enables swapping simulator ↔ Massive without changing downstream code
- Examples: `backend/market/simulator.py:SimulatorProvider`, `backend/market/massive.py:MassiveProvider`
- Pattern: ABC with abstract methods; concrete implementations override `start()`, `stop()`, `get_prices()`, `update_tickers()`
- Ensures: Consistent interface for price queries and background task management
- Purpose: Immutable data class representing a single price observation
- Examples: Yielded by simulator tick; returned by provider.get_prices()
- Pattern: Frozen dataclass (hashable, thread-safe conceptually though not needed here)
- Fields: ticker, price, prev_price, change_pct, timestamp
- Purpose: Structured output from LLM; validated at parse time
- Examples: `backend/llm/schema.py:ChatCompletion`
- Pattern: Pydantic BaseModel with nested ChatTrade and WatchlistChange models
- Ensures: Type-safe access to message, trades, and watchlist_changes; failures during parsing caught early
- Purpose: User-facing trade validation exception
- Examples: "Insufficient cash", "Invalid side", "No live price"
- Pattern: Custom exception with message safe to return in HTTP 400 response
- Ensures: Graceful error reporting; trade never executes partially on validation failure

## Entry Points

- Location: `/` (root path)
- Triggers: User navigates to `http://localhost:8000`
- Responsibilities: FastAPI serves static `index.html` from frontend build; browser loads SPA; hooks initialize (price stream, initial data load)
- Location: `backend/api/health.py:get_health()`
- Triggers: GET `/api/health`
- Responsibilities: Returns `{"status": "ok", "market_provider": "simulator" | "massive"}`; used by Docker for liveness probes
- Location: `backend/api/portfolio.py:get_portfolio()`
- Triggers: GET `/api/portfolio`
- Responsibilities: Aggregates current positions, cash, total value, P&L from repository and prices
- Location: `backend/api/portfolio.py:post_trade()`
- Triggers: POST `/api/portfolio/trade` with TradeRequest (ticker, quantity, side)
- Responsibilities: Validates, executes, records, snapshots, returns updated context
- Location: `backend/api/portfolio.py:get_history()`
- Triggers: GET `/api/portfolio/history`
- Responsibilities: Returns array of portfolio snapshots for P&L chart
- Location: `backend/api/watchlist.py:*`
- Triggers: GET/POST/DELETE `/api/watchlist[/{ticker}]`
- Responsibilities: List, add, remove tickers; update market provider on change
- Location: `backend/api/stream.py:stream_prices()`
- Triggers: GET `/api/stream/prices` (opens EventSource connection)
- Responsibilities: Yields price updates every 0.5s; server keeps connection open until client disconnects
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

### Trade Execution Without Atomicity

```python

```

### Unbounded Price History on Frontend

### No Validation of Watchlist Ticker Format

### Chat Auto-Execution Proceeds After LLM Parse Failure

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| cerebras-inference | Use this to write code to call an LLM using LiteLLM and OpenRouter with the Cerebras inference provider | `.claude/skills/cerebras/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
