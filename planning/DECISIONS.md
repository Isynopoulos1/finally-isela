# Build Decisions

Resolves the open questions and simplification opportunities raised in PLAN.md §13.
All team members must build against these decisions, not the raw §13 discussion.

1. **SSE stream scope**: `/api/stream/prices` pushes updates only for tickers currently
   on the watchlist (there is no broader universe). Backend calls
   `provider.update_tickers(...)` whenever the watchlist changes.

2. **Main chart data source**: The main chart (and sparklines) are built entirely from
   SSE data accumulated on the frontend since page load. No `/api/prices/{ticker}/history`
   endpoint. Resetting on browser refresh is explicitly acceptable for this course project.

3. **LLM model / provider**: Do not hardcode a guessed model id. Use the `cerebras` skill
   (LiteLLM → OpenRouter → Cerebras) as the source of truth for the model id and call
   pattern when implementing `backend/llm/`.

4. **Charting library**: Lightweight Charts (canvas-based) for both the sparklines and the
   main chart. Do not use Recharts.

5. **Watchlist structured-output actions**: `watchlist_changes[].action` supports both
   `"add"` and `"remove"`.

6. **Schema simplification**: No `user_id` columns anywhere (single-user app, no auth).
   `users_profile` is a singleton row for `cash_balance`. `watchlist`, `positions`,
   `trades`, `portfolio_snapshots`, `chat_messages` have no user reference column at all.

7. **portfolio_snapshots**: Snapshot-on-trade only. No 30-second background polling task.
   Also record one snapshot at DB seed time so the P&L chart has an initial point.

8. **Market data**: Already implemented in `backend/market/` (simulator + Massive client
   behind `MarketDataProvider`, selected by `market/factory.py`). Do not rebuild — import
   and use it as-is. See `market/interface.py` for the contract.

9. **E2E tests**: Playwright runs locally against `uvicorn` (backend, serving the built
   static frontend) with `LLM_MOCK=true`. The `docker-compose.test.yml` container-based
   approach from PLAN.md §12 is a stretch goal only, not required for the initial build.

10. **chat_messages.actions**: Store as a plain human-readable summary string
    (e.g. `"Bought 10 AAPL @ $190.32"`), not a structured JSON blob. Column name
    `action_summary`, nullable TEXT.

## Ownership boundaries

- **Database Engineer** — `backend/db/`: schema, lazy init + seed, and a small repository
  module (plain functions, no ORM) that every other backend module imports for reads/writes.
- **Backend API Engineer** — `backend/main.py` (FastAPI app), `backend/api/` routers for
  health, portfolio, watchlist, and the SSE stream; static file serving of the built
  frontend. Owns the shared trade-execution function and portfolio-context builder that
  the LLM engineer reuses. Registers an empty `backend/api/chat.py` router stub (just
  `POST /api/chat` returning 501) so the LLM engineer can fill it in without touching
  `main.py`.
- **LLM Engineer** — `backend/llm/`: OpenRouter/Cerebras call via the `cerebras` skill,
  structured output schema, mock mode, fills in `backend/api/chat.py` using the backend
  engineer's trade-execution and portfolio-context functions plus the DB engineer's
  chat_messages repository functions.
- **Frontend Engineer** — `frontend/`: Next.js static export, all UI panels from PLAN.md
  §10, Lightweight Charts, Tailwind dark theme, EventSource SSE client.
- **DevOps Engineer** — `Dockerfile`, `docker-compose.yml`, `scripts/`, `.dockerignore`.
- **Integration Tester** — `test/`: Playwright E2E tests per PLAN.md §12 scenarios, run
  against the locally built app with `LLM_MOCK=true`; reports bugs back for the owning
  engineer to fix.
