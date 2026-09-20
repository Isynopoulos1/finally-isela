---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# External Integrations

**Analysis Date:** 2026-09-20

## APIs & External Services

**LLM & AI:**

- OpenRouter - AI inference platform providing access to Cerebras and other models
  - SDK/Client: LiteLLM 1.101.0+ (via `backend/llm/client.py`)
  - Auth: Environment variable `OPENROUTER_API_KEY`
  - Model: `openrouter/openai/gpt-oss-120b` with Cerebras as the preferred inference provider
  - Purpose: Chat assistant that analyzes portfolio and executes trades/watchlist changes via structured JSON output
  - Implementation: `backend/api/chat.py` → `call_llm()` in `backend/llm/client.py` → LiteLLM completion call

**Market Data (Optional Live):**

- Massive API (Polygon.io) - REST API for multi-ticker stock price snapshots
  - SDK/Client: httpx 0.27+ for async HTTP calls
  - Auth: Environment variable `MASSIVE_API_KEY`
  - Endpoint: `https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers`
  - Purpose: Real-time market data when API key is configured; otherwise built-in simulator is used
  - Implementation: `backend/market/massive.py` → MassiveProvider class
  - Polling interval: Configurable via `MASSIVE_POLL_INTERVAL_SECONDS` env var (default 15s), adjusted for API tier (free: 5 req/min)
  - Fallback: Disabled and logs retry if endpoint returns rate-limit errors

## Data Storage

**Databases:**

- SQLite 3 - Embedded database for all persistent data
  - Connection: `backend/db/connection.py` → lazy-initialized at `db/finally.db` (volume-mounted in Docker at `/app/db`)
  - Client: stdlib `sqlite3` module (no ORM)
  - Initialization: Automatic schema creation and seed data on first connection via `db/schema.py` and `db/seed.py`
  - Tables: `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `chat_messages` (see `backend/db/schema.py`)
  - Features: Row factory enabled for dict-like access, check_same_thread=False for async context

**File Storage:**

- Local filesystem only
  - Frontend static build output: `backend/static/` (copied from `frontend/out/` during Docker build)
  - SQLite file: Docker volume at `/app/db/finally.db`
  - No cloud storage integration

**Caching:**

- In-memory cache only
  - Price cache in `MarketDataProvider` (simulator or Massive) - dictionary of latest `PriceUpdate` objects per ticker
  - No Redis or external cache layer
  - Cache is populated by background task (simulator or Massive poller) and read by SSE endpoint

## Authentication & Identity

**Auth Provider:**

- None (single-user application)
  - All database tables have a `user_id` column defaulting to `"default"` for future multi-user support
  - No login, no signup, no session management
  - All users share the same `user_id="default"` hardcoded in seed data

## Real-Time Communication

**Server-Sent Events (SSE):**

- Endpoint: `GET /api/stream/prices` (`backend/api/stream.py`)
- Protocol: HTTP/1.1 with `text/event-stream` content type
- Behavior: Server pushes price updates for all watched tickers at regular cadence (~500ms)
- Client: Browser native `EventSource` API for automatic reconnection
- Data format: JSON events with ticker, price, prev_price, change_pct, timestamp
- Bidirectionality: One-way server → client push only

## Monitoring & Observability

**Error Tracking:**

- None implemented
  - LLM call errors caught at `backend/api/chat.py:99-104` and returned as user-facing error message
  - Massive API errors logged but allow graceful degradation

**Logging:**

- Python stdlib `logging` module
  - Market providers log at INFO level: "Massive provider started", "No MASSIVE_API_KEY" (see `backend/market/factory.py`)
  - Detailed module-level loggers for debugging (e.g., `log = logging.getLogger(__name__)`)
  - No structured logging, no centralized log aggregation

**Health Checks:**

- Endpoint: `GET /api/health` (`backend/api/health.py`)
  - Returns: JSON with status and uptime for monitoring/orchestration

## CI/CD & Deployment

**Hosting:**

- Docker container (single image deployable to any container platform)
- Local development: Docker Compose (`docker-compose.yml`) with volume mount for SQLite persistence
- Production deployment: Docker run with env-file and volume

**CI Pipeline:**

- Not detected (no GitHub Actions, no CI config in repo)
- Docker build via `Dockerfile` (multi-stage: Node → Python)

**Scripts:**

- `scripts/start_mac.sh` - Bash script to build and run Docker container (macOS/Linux)
- `scripts/stop_mac.sh` - Bash script to stop container
- `scripts/start_windows.ps1` - PowerShell equivalent for Windows
- `scripts/stop_windows.ps1` - PowerShell equivalent for Windows

## Environment Configuration

**Required Environment Variables:**

- `OPENROUTER_API_KEY` - OpenRouter API key for LLM chat (no default; chat will fail if missing)

**Optional Environment Variables:**

- `MASSIVE_API_KEY` - Polygon.io/Massive API key; if absent/empty, simulator is used (recommended for most users)
- `LLM_MOCK` - Set to `"true"` to return deterministic mock LLM responses (for E2E tests); default `"false"`
- `MASSIVE_POLL_INTERVAL_SECONDS` - Override default 15-second polling interval for Massive API

**Secrets Location:**

- `.env` file in project root (git-ignored)
- `.env.example` committed with documentation of required/optional vars
- Docker build: env vars loaded via `--env-file .env` flag when running container
- Backend: `python-dotenv` loads `.env` at `backend/llm/client.py:load_dotenv()`

## Webhooks & Callbacks

**Incoming Webhooks:**

- Not implemented
  - No external services push data to the app

**Outgoing Webhooks:**

- Not implemented
  - No callbacks to external services triggered by trades or portfolio changes

## Price Data Flow

**Simulator Path (Default):**

1. Background task in `backend/market/simulator.py` → generates prices using geometric Brownian motion
2. Updates in-memory cache every ~500ms
3. SSE endpoint reads cache and pushes to all connected clients
4. Frontend accumulates prices into sparklines and chart data

**Massive API Path (When MASSIVE_API_KEY set):**

1. Background task in `backend/market/massive.py` polls REST endpoint every 15s (configurable)
2. Parses response into `PriceUpdate` objects
3. Updates in-memory cache
4. SSE endpoint reads cache and pushes to clients
5. Same frontend behavior

**Shared Interface:**

- Both implementations conform to `backend/market/interface.py` → `MarketDataProvider` abstract class
- Downstream code (portfolio valuation, SSE streaming) is provider-agnostic

---

*Integration audit: 2026-09-20*
