---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# Codebase Structure

**Analysis Date:** 2026-09-20

## Directory Layout

```
finally/
├── frontend/                    # Next.js SPA (TypeScript, React 18, Tailwind)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout (head, Tailwind config)
│   │   │   └── page.tsx         # Home page (main UI, state management)
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Header.tsx       # Portfolio value, connection status, cash
│   │   │   ├── Watchlist.tsx    # Grid of watched tickers
│   │   │   ├── WatchlistRow.tsx # Single ticker with price, sparkline
│   │   │   ├── MainChart.tsx    # Large chart for selected ticker
│   │   │   ├── PriceChart.tsx   # Chart rendering wrapper (Recharts)
│   │   │   ├── TradeBar.tsx     # Buy/sell input form
│   │   │   ├── PositionsTable.tsx # Holdings detail table
│   │   │   ├── PortfolioHeatmap.tsx # Treemap visualization
│   │   │   ├── PnlChart.tsx     # Portfolio value over time line chart
│   │   │   ├── ChatPanel.tsx    # Chat UI (messages, input, loading)
│   │   │   └── __tests__/       # Component tests (React Testing Library)
│   │   ├── lib/
│   │   │   ├── api.ts           # Fetch wrapper for all /api/* endpoints
│   │   │   ├── types.ts         # TypeScript interfaces (Portfolio, Position, etc)
│   │   │   ├── format.ts        # Display formatting (currency, percent, date)
│   │   │   ├── treemap.ts       # Treemap layout algorithm for heatmap
│   │   │   └── usePriceStream.ts# Hook: EventSource connection & price history
│   │   └── globals.css          # Tailwind + custom CSS (dark theme)
│   ├── public/                  # Static assets (favicons, images)
│   ├── out/                     # Static export build output (git-ignored)
│   ├── next.config.js           # Next.js config (static export, no server)
│   ├── tsconfig.json            # TypeScript config
│   ├── tailwind.config.ts       # Tailwind CSS config (dark mode, colors)
│   ├── package.json             # Dependencies
│   └── .env.local (git-ignored) # NEXT_PUBLIC_API_BASE_URL
│
├── backend/                     # FastAPI app (Python 3.12, uv project)
│   ├── main.py                  # FastAPI app definition, lifespan, router registration
│   ├── api/                     # API route modules (one router per feature)
│   │   ├── __init__.py
│   │   ├── health.py            # GET /api/health
│   │   ├── portfolio.py         # GET/POST /api/portfolio*, GET /api/portfolio/history
│   │   ├── watchlist.py         # GET/POST/DELETE /api/watchlist*
│   │   ├── stream.py            # GET /api/stream/prices (SSE)
│   │   └── chat.py              # POST /api/chat
│   ├── portfolio/               # Business logic: trading
│   │   ├── __init__.py
│   │   ├── trading.py           # execute_trade() function
│   │   └── context.py           # build_portfolio_context() aggregation
│   ├── llm/                     # LLM integration
│   │   ├── __init__.py
│   │   ├── client.py            # call_llm() via OpenRouter (LiteLLM)
│   │   ├── prompt.py            # build_messages() for LLM context
│   │   ├── schema.py            # ChatCompletion, ChatTrade, WatchlistChange (Pydantic)
│   │   └── mock.py              # mock_response() for testing
│   ├── market/                  # Price data abstraction
│   │   ├── __init__.py
│   │   ├── interface.py         # MarketDataProvider ABC, PriceUpdate dataclass
│   │   ├── factory.py           # make_provider() factory function
│   │   ├── simulator.py         # SimulatorProvider (in-process GBM)
│   │   ├── massive.py           # MassiveProvider (Polygon.io REST API)
│   │   └── tickers.py           # normalize() utility, SEED_PRICES
│   ├── db/                      # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py        # get_connection() singleton pattern
│   │   ├── schema.py            # init_db(), DDL string
│   │   ├── seed.py              # seed_db() initial data
│   │   └── repository.py        # Data access functions (CRUD, no ORM)
│   ├── tests/                   # pytest test suite
│   │   ├── __init__.py
│   │   ├── conftest.py          # pytest fixtures (test DB, mock client)
│   │   ├── test_api_*.py        # API endpoint tests
│   │   ├── test_db_*.py         # Database layer tests
│   │   ├── test_market_*.py     # Market provider tests (simulator, massive, interface)
│   │   ├── test_portfolio_*.py  # Trading logic tests
│   │   └── test_llm_*.py        # LLM client & schema tests
│   ├── static/                  # Populated by Docker: frontend build output
│   │   └── (Next.js export contents at runtime)
│   ├── pyproject.toml           # uv project config, dependencies, metadata
│   ├── uv.lock                  # Locked dependency versions
│   └── .env (git-ignored)       # OPENROUTER_API_KEY, MASSIVE_API_KEY, LLM_MOCK
│
├── test/                        # E2E test suite (Playwright)
│   ├── e2e/
│   │   ├── *.spec.ts            # Playwright test cases
│   │   └── fixtures/            # Test data, helper functions
│   ├── docker-compose.test.yml  # Optional: dedicated test infrastructure
│   ├── package.json             # Playwright + test dependencies
│   └── playwright.config.ts     # Playwright config
│
├── db/                          # Volume mount point (runtime only)
│   ├── .gitkeep                 # Directory tracked in git
│   └── finally.db (git-ignored) # SQLite file created by backend at runtime
│
├── scripts/                     # Docker start/stop convenience scripts
│   ├── start_mac.sh             # ./scripts/start_mac.sh [--build]
│   ├── stop_mac.sh              # ./scripts/stop_mac.sh
│   ├── start_windows.ps1        # PowerShell equivalent
│   └── stop_windows.ps1
│
├── planning/                    # Project-wide documentation for agents
│   ├── PLAN.md                  # Full project spec (vision, UX, architecture, API, etc)
│   ├── MARKET_DATA_SUMMARY.md   # Market data component summary
│   ├── archive/                 # Historical docs
│   └── ...
│
├── .claude/                     # Claude Code workspace config
│   └── agents/                  # Agent definitions for GSD orchestration
├── .github/                     # GitHub Actions workflows (CI/CD)
├── .env.example                 # Example environment variables (committed)
├── .env (git-ignored)           # Actual environment variables
├── .gitignore
├── Dockerfile                   # Multi-stage build (Node → Python)
├── docker-compose.yml           # Optional Docker Compose wrapper
└── README.md                    # Project overview (brief)
```

## Directory Purposes

**`frontend/src/`:**

- Purpose: React SPA source code
- Contains: Components, hooks, API client, utilities, types, styles
- Key files: `app/page.tsx` (root component), `components/` (reusable UI), `lib/` (logic)

**`frontend/src/components/`:**

- Purpose: Reusable React components
- Contains: Header, Watchlist, MainChart, TradeBar, PositionsTable, PortfolioHeatmap, PnlChart, ChatPanel, Price- and Watchlist-related sub-components
- Key files: See directory listing above; each component is a `.tsx` file exporting a default function

**`frontend/src/lib/`:**

- Purpose: Non-UI utilities, API client, hooks, types
- Contains: `api.ts` (fetch wrapper), `types.ts` (TypeScript interfaces), `usePriceStream.ts` (SSE hook), `format.ts` (display utilities), `treemap.ts` (layout algorithm)
- Key files: `types.ts` (single source of truth for all data types), `api.ts` (all backend calls), `usePriceStream.ts` (real-time data ingestion)

**`backend/api/`:**

- Purpose: FastAPI route handlers (request → response)
- Contains: One module per feature (health, portfolio, watchlist, stream, chat)
- Each file defines a FastAPI `APIRouter` and registers routes
- Key files: `portfolio.py` (trade execution entry point), `chat.py` (LLM integration entry point), `stream.py` (SSE generator)

**`backend/portfolio/`:**

- Purpose: Trading and portfolio business logic (no API)
- Contains: `trading.py` (execute_trade, TradeError), `context.py` (build_portfolio_context)
- Key files: `trading.py` (core trade validation and execution)

**`backend/llm/`:**

- Purpose: LLM integration and structured response handling
- Contains: OpenRouter client via LiteLLM, prompt construction, schema validation, mock responses
- Key files: `schema.py` (Pydantic models for request/response), `client.py` (call_llm function), `prompt.py` (system prompt + context), `mock.py` (deterministic mock for testing)

**`backend/market/`:**

- Purpose: Market data abstraction (simulator or Massive API)
- Contains: Provider interface, two concrete implementations, factory function, ticker utilities
- Key files: `interface.py` (MarketDataProvider ABC), `simulator.py` (GBM generator), `massive.py` (Polygon.io REST client), `factory.py` (env-based selection)

**`backend/db/`:**

- Purpose: Database schema and data access (single-user SQLite)
- Contains: DDL, initialization, seed data, repository functions
- Key files: `schema.py` (table definitions), `repository.py` (all CRUD functions), `connection.py` (get_connection singleton), `seed.py` (default data)

**`backend/tests/`:**

- Purpose: pytest test suite
- Contains: Unit tests for API, database, market, portfolio, LLM modules
- Naming: `test_<module>_<function>.py` or `test_<module>.py` for grouped tests
- Key files: `conftest.py` (pytest fixtures, in-memory DB for tests)

**`test/e2e/`:**

- Purpose: Playwright end-to-end tests
- Contains: Browser automation tests covering user workflows (watchlist, trades, chat, etc)
- Naming: `*.spec.ts` (Playwright convention)

**`db/`:**

- Purpose: Runtime SQLite volume mount point
- Contains: Nothing in git (except `.gitkeep`); `finally.db` created by backend at runtime
- Persistence: Volume-mounted in Docker so data survives container restarts

**`scripts/`:**

- Purpose: Convenience wrappers around Docker commands
- Contains: Start/stop shell scripts for macOS/Linux and PowerShell for Windows
- Key files: `start_mac.sh` (builds & runs container), `stop_mac.sh` (stops container)

**`planning/`:**

- Purpose: Project documentation for AI agents
- Contains: PLAN.md (full spec), MARKET_DATA_SUMMARY.md (component status), archive (old docs)
- Usage: Agents reference these docs to understand requirements and architecture

## Key File Locations

**Entry Points:**

- Browser entry: `frontend/src/app/page.tsx` (Home component, root of SPA)
- Backend entry: `backend/main.py` (FastAPI app creation, lifespan, routers)
- Docker entry: `Dockerfile` (multi-stage build)

**Configuration:**

- Next.js: `frontend/next.config.js` (static export, no server runtime)
- TypeScript (frontend): `frontend/tsconfig.json`
- Tailwind CSS: `frontend/tailwind.config.ts` (dark theme, custom colors)
- Python: `backend/pyproject.toml` (uv project, dependencies)
- Pytest: `backend/tests/conftest.py` (fixtures)
- Playwright: `test/playwright.config.ts` (browser, baseURL, timeout)
- Docker: `Dockerfile` (Node 24 + Python 3.12 stages)

**Core Logic:**

- Trade execution: `backend/portfolio/trading.py:execute_trade()`
- Portfolio aggregation: `backend/portfolio/context.py:build_portfolio_context()`
- LLM call: `backend/llm/client.py:call_llm()`
- Price stream: `backend/api/stream.py:stream_prices()`
- Market data: `backend/market/interface.py` (abstract), `backend/market/simulator.py`, `backend/market/massive.py`
- API client: `frontend/src/lib/api.ts`

**Testing:**

- Backend tests: `backend/tests/` (pytest)
- Frontend tests: `frontend/src/components/__tests__/` (React Testing Library)
- E2E tests: `test/e2e/` (Playwright)
- Test fixtures: `backend/tests/conftest.py`, `test/e2e/fixtures/`

## Naming Conventions

**Files:**

- Python modules: `snake_case.py` (e.g., `trading.py`, `api/portfolio.py`)
- TypeScript modules: `camelCase.tsx` or `snake_case.ts` (components use PascalCase: `Header.tsx`, utilities use camelCase: `usePriceStream.ts`)
- Test files: `test_<module>.py` (backend) or `<component>.test.tsx` (frontend), `*.spec.ts` (Playwright)

**Directories:**

- Feature packages: lowercase plural (e.g., `backend/api/`, `backend/portfolio/`, `backend/market/`)
- Built/generated: `out/` (Next.js), `static/` (backend-served frontend), `__pycache__/` (Python)
- Test directories: `tests/` (backend), `__tests__/` (frontend), `e2e/` (Playwright)

**Python:**

- Functions: `snake_case` (e.g., `execute_trade`, `build_portfolio_context`, `get_connection`)
- Classes: `PascalCase` (e.g., `SimulatorProvider`, `TradeError`, `ChatCompletion`)
- Constants: `UPPER_CASE` (e.g., `TICK_SECONDS`, `ANNUAL_DRIFT`, `SEED_PRICES`)
- Private/internal: Leading underscore (e.g., `_apply_trades`, `_seed`, `_now`)

**TypeScript/React:**

- Components: `PascalCase` (e.g., `Header`, `Watchlist`, `ChatPanel`)
- Hooks: `useCamelCase` (e.g., `usePriceStream`, `useState`)
- Functions: `camelCase` (e.g., `buildPortfolioContext`, `getWatchlist`)
- Types/interfaces: `PascalCase` (e.g., `Portfolio`, `Position`, `ChatMessage`)
- Constants: `UPPER_CASE` or `camelCase` depending on scope (module-level are UPPER_CASE)

## Where to Add New Code

**New Feature (Backend):**

- Primary code: Create module in `backend/<feature>/` (e.g., `backend/alerts/` for alert system)
- API route: Add router in `backend/api/<feature>.py` and register in `backend/main.py` with `app.include_router()`
- Tests: Add tests in `backend/tests/test_<feature>.py`
- Database: If data storage needed, add table in `backend/db/schema.py` and functions in `backend/db/repository.py`
- Business logic: Keep in `backend/<feature>/` module, separate from API routes

**New Feature (Frontend):**

- Primary code: Create components in `frontend/src/components/` if reusable; or add to `frontend/src/app/page.tsx` if page-level
- Utilities/hooks: Add to `frontend/src/lib/` (e.g., new hook in `frontend/src/lib/useNewFeature.ts`)
- Types: Add to `frontend/src/lib/types.ts`
- Tests: Add `frontend/src/components/__tests__/<Component>.test.tsx` for component tests
- Styles: Use Tailwind classes in components; custom CSS in `frontend/src/globals.css` only for theme/overrides

**New Component/Module:**

- Backend service: Create `backend/<service>/` with module interface and implementation(s)
- Frontend component: Create `frontend/src/components/<Component>.tsx` with all styles inline (Tailwind) or in `globals.css` if shared

**Utilities:**

- Shared helpers (backend): `backend/<module>/utils.py` or place directly in module if small
- Shared helpers (frontend): `frontend/src/lib/` (e.g., `format.ts`, `treemap.ts` for algorithms)

**Database Changes:**

- Schema: Modify DDL in `backend/db/schema.py` (add table or column)
- Seed: Add default data in `backend/db/seed.py`
- Access: Add functions to `backend/db/repository.py`
- Important: Lazy initialization means old databases won't auto-migrate; add migration logic to `backend/db/connection.py:get_connection()` if backward compatibility needed

**Environment Variables:**

- Add to `.env.example` (committed) with explanation
- Backend reads from `.env` file automatically (python-dotenv)
- Frontend (Next.js): prefix with `NEXT_PUBLIC_` to expose to browser; set in `.env.local` at build time

**Tests:**

- Backend unit tests: `backend/tests/test_<module>.py`
- Frontend component tests: `frontend/src/components/__tests__/<Component>.test.tsx`
- E2E tests: `test/e2e/<feature>.spec.ts`
- Run tests: `pytest` (backend), `npm test` (frontend), `npm run test:e2e` (E2E)

## Special Directories

**`frontend/out/`:**

- Purpose: Next.js static export build output
- Generated: `npm run build` in `frontend/`
- Committed: No (`.gitignore`)
- Copied to backend: `Dockerfile` Stage 1 copies to `backend/static/` for serving

**`backend/static/`:**

- Purpose: Frontend build output served by FastAPI at runtime
- Generated: Populated by Dockerfile multi-stage copy
- Committed: No (`.gitignore`)
- Served as: Mounted at root `/` by FastAPI's `StaticFiles` handler

**`db/`:**

- Purpose: SQLite database volume mount point
- Generated: Backend creates `db/finally.db` at runtime
- Committed: No (only `.gitkeep` in git)
- Persistence: Named Docker volume or host bind mount

**`backend/.venv/`:**

- Purpose: Python virtual environment (if `uv` uses one locally)
- Generated: `uv sync` (or `uv venv` manually)
- Committed: No (`.gitignore`)
- In Docker: Not used; `uv` syncs directly into system Python

**`test/node_modules/`, `frontend/node_modules/`:**

- Purpose: npm dependencies
- Generated: `npm install` or `npm ci`
- Committed: No (`.gitignore`)
- Lockfiles committed: `package-lock.json` for reproducibility

**`.claude/agents/`:**

- Purpose: GSD agent definitions for orchestration
- Generated: By agent setup / onboarding
- Committed: Yes
- Usage: Defines personas and workflows for CI/CD agents

---

*Structure analysis: 2026-09-20*
