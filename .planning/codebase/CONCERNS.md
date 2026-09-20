---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# Codebase Concerns

**Analysis Date:** 2026-09-20

## Tech Debt

**LLM Exception Handling - Incomplete Coverage:**

- Issue: `backend/api/chat.py` catches only `OpenAIError` and `ValueError`, but LiteLLM raises many exception types (`litellm.RateLimitError`, `litellm.APIError`, `litellm.APIConnectionError`, `litellm.ModelNotFoundError`, etc.)
- Files: `backend/api/chat.py` (lines 99-104)
- Impact: Network failures, rate limits, and API errors from LiteLLM won't be caught. The app will crash with unhandled exceptions instead of returning a graceful error message to the user
- Fix approach: Import `litellm` exceptions and catch the base exception class, or catch all exceptions more broadly. Add specific handling for timeout and rate limit scenarios

**Frontend Async Error Handling - Silent Failures:**

- Issue: Main page handlers (`handleAddTicker`, `handleRemoveTicker`, `handleTrade`) lack error handling. Errors are silently swallowed with `.catch(() => {})`
- Files: `frontend/src/app/page.tsx` (lines 75-89)
- Impact: Users see no feedback when a ticker add/remove or trade fails. They believe the operation succeeded when it actually failed
- Fix approach: Add error state management and display error messages to the user in each handler. Show a toast or inline error message

**WatchlistRow Remove Error Handling - No User Feedback:**

- Issue: `WatchlistRow` component's `onRemove` callback has no error handling wrapper. Parent component (`Watchlist`) catches the error, but the component-level handler doesn't provide feedback
- Files: `frontend/src/components/WatchlistRow.tsx` (line 82)
- Impact: If removing a ticker fails, no visual feedback is given, and the row may remain in the list
- Fix approach: Wrap the `onRemove` call in a try-catch and set error state in the parent. Show a transient error message next to the remove button

**SQLite Thread Safety Configuration:**

- Issue: `backend/db/connection.py` uses `check_same_thread=False` for SQLite, which disables thread safety checks
- Files: `backend/db/connection.py` (line 31)
- Impact: If FastAPI spawns threads for any reason (e.g., via threadpool executors), concurrent access to SQLite could cause database corruption
- Fix approach: Review FastAPI's async model and confirm no thread spawning occurs. If using thread executors, remove `check_same_thread=False` and implement proper locking

**LLM Client - No Timeout Configuration:**

- Issue: `backend/llm/client.py` calls LiteLLM's `completion()` without an explicit timeout parameter
- Files: `backend/llm/client.py` (lines 16-26)
- Impact: LLM requests can hang indefinitely, blocking the chat endpoint and accumulating zombie requests
- Fix approach: Add `timeout=30.0` (or appropriate duration) to the `completion()` call

**Massive API - JSON Parsing Without Error Handling:**

- Issue: `backend/market/massive.py` calls `resp.json()` without try-catch, assuming the API response is valid JSON
- Files: `backend/market/massive.py` (line 99)
- Impact: If the API returns malformed JSON (e.g., HTML error page on a 5xx), the app will crash with `JSONDecodeError`
- Fix approach: Wrap `resp.json()` in try-catch and log the error. Treat malformed responses as an API error and retry on the next poll interval

**Division by Zero Risk - Unrealized P&L Calculation:**

- Issue: `backend/portfolio/context.py` divides by `position["avg_cost"]` without checking if it's zero
- Files: `backend/portfolio/context.py` (line 41)
- Impact: If a position is created with `avg_cost = 0` (due to data corruption or edge case), P&L calculation will crash
- Fix approach: Add a guard `if position["avg_cost"] != 0` before the division, or initialize avg_cost with a minimum floor of 0.01

---

## Known Bugs

**Frontend Page State Not Reset on Error:**

- Symptoms: After a failed chat message, the draft text is cleared (line 21 in `ChatPanel.tsx`), but if that API call fails, the user message is still added to the UI, leading to orphaned user messages without assistant responses
- Files: `frontend/src/app/page.tsx` (lines 91-119)
- Trigger: Send a chat message, then experience a network failure or LLM service outage
- Workaround: User must manually clear the chat history or reload the page. For now, display an error message to the user instead of silently failing

**Watchlist Add Doesn't Validate Ticker Before API Call:**

- Symptoms: User can add an invalid ticker (e.g., `"!!!"`), and the backend rejects it, but the frontend shows a generic error with no guidance
- Files: `frontend/src/components/Watchlist.tsx` (lines 31-37)
- Trigger: Type an invalid character in the add-ticker field and click Add
- Workaround: Let the backend validation handle it, but improve the error message to indicate why the ticker is invalid

**Race Condition in Watchlist Updates:**

- Symptoms: If a user adds a ticker while `handleAddTicker` is running, and the ticker normalization differs between frontend and backend, the displayed watchlist may not match what's in the database
- Files: `frontend/src/app/page.tsx` (line 77) and `backend/market/tickers.py`
- Trigger: Add a ticker (e.g., "aapl") and immediately add another while the first request is in-flight
- Workaround: Await the watchlist refresh before allowing another add. Add debouncing if needed

---

## Security Considerations

**LLM Auto-Execution of Trades Without Confirmation:**

- Risk: The LLM can execute trades autonomously without explicit user confirmation. A misinterpreted prompt could result in large unintended trades
- Files: `backend/api/chat.py` (lines 106-107)
- Current mitigation: This is simulated money in a demo, so financial loss is not a concern. However, the capability is concerning for production use
- Recommendations: For production, add a confirmation step for LLM-initiated trades above a certain quantity or value. Log all LLM-initiated actions for audit purposes

**No Rate Limiting on API Endpoints:**

- Risk: The API has no rate limiting. A malicious client could flood the server with requests, causing denial of service
- Files: `backend/main.py` (no rate limiting middleware)
- Current mitigation: Deployed behind a single Docker container on localhost; not exposed to the public internet
- Recommendations: Add `slowapi` or FastAPI middleware for rate limiting before production deployment. Implement per-user or per-IP limits

**Environment Secrets in .env File:**

- Risk: The `.env` file contains `OPENROUTER_API_KEY`, which should never be committed to git
- Files: `.env` (exists but is in `.gitignore`)
- Current mitigation: Correctly ignored by git
- Recommendations: Document `.env.example` with placeholder values. Use Docker secrets or environment variable injection for production. Never commit `.env`

**No Input Validation on Ticker Field:**

- Risk: Ticker input is normalized but not validated against a known list. Typos or typosquatting are possible
- Files: `backend/market/tickers.py`
- Current mitigation: Massive API would reject invalid tickers; simulator accepts any ticker and seeds it with a default price
- Recommendations: Maintain a whitelist of valid tickers. Reject additions of unknown tickers with clear feedback

---

## Performance Bottlenecks

**Synchronous Database Access Pattern:**

- Problem: Every endpoint calls `get_connection()` and performs synchronous SQL operations. While SQLite is fast, blocking I/O in an async context is suboptimal
- Files: `backend/db/repository.py` (all functions)
- Cause: Repository functions use synchronous SQLite calls within async FastAPI handlers. No connection pooling or prepared statements
- Improvement path: Use `sqlalchemy` with async support (e.g., `sqlalchemy[asyncio]`) or `aiosqlite` for true async database access. This would allow concurrent requests without blocking

**Portfolio Recalculation on Every Request:**

- Problem: `build_portfolio_context()` recalculates the entire portfolio (market values, P&L) on every `/api/portfolio` call
- Files: `backend/portfolio/context.py`
- Cause: No caching; all positions are fetched from the database and recalculated
- Improvement path: Cache the portfolio context for 1-5 seconds. Invalidate the cache when a trade is executed. This would dramatically reduce database pressure

**SSE Stream Sends All Tickers Every 500ms:**

- Problem: The `/api/stream/prices` endpoint sends **all** tracked tickers every 500ms to every connected client, even if the client only cares about a subset
- Files: `backend/api/stream.py` (lines 20-28)
- Cause: One-size-fits-all approach; no per-client subscription
- Improvement path: Allow clients to subscribe to specific tickers via query parameters. Send only subscribed tickers in the stream

**Frontend Poll Intervals Could Overwhelm Backend:**

- Problem: Portfolio and history are polled every 4-10 seconds from every client. With many clients, this becomes a throughput issue
- Files: `frontend/src/app/page.tsx` (lines 16-17)
- Cause: No backoff or adaptive polling
- Improvement path: Use WebSocket or longer-lived SSE for state updates instead of polling. Reduce poll frequency based on market activity

**Watchlist Refresh After Every Trade:**

- Problem: `handleTrade` refreshes both portfolio and watchlist unnecessarily after a trade (line 88)
- Files: `frontend/src/app/page.tsx`
- Cause: Defensive refresh; watchlist doesn't change during a trade
- Improvement path: Only refresh the portfolio and history. Skip the watchlist refresh unless a ticker was added/removed

---

## Fragile Areas

**LLM Response Parsing - Fragile JSON Deserialization:**

- Files: `backend/llm/client.py` (line 26)
- Why fragile: The LLM response is parsed with `ChatCompletion.model_validate_json()` which will raise a `ValidationError` if the response doesn't match the schema. If the LLM ever returns a slightly different format, the chat endpoint crashes
- Safe modification: Add a try-catch around the validation and return a fallback `ChatCompletion` with just the message field on validation failure
- Test coverage: Gaps — no tests for malformed LLM responses

**Market Provider Startup - No Fallback:**

- Files: `backend/main.py` (lines 19-22)
- Why fragile: If `provider.start()` fails (e.g., network error fetching first price from Massive), the entire app fails to start and becomes unreachable
- Safe modification: Wrap `provider.start()` in try-catch. If it fails, log a warning and continue with an empty cache. The cache will populate on the first successful poll
- Test coverage: Gaps — no tests for provider startup failure

**Seed Data Assumption - Only if Empty:**

- Files: `backend/db/seed.py` (line 13)
- Why fragile: Seeds only if `users_profile` is empty. If a user accidentally deletes their profile but leaves watchlist entries, seeding won't restore the profile, leading to orphaned data
- Safe modification: Add a data integrity check after seeding. If watchlist exists without a profile, either clean up the watchlist or re-seed the profile
- Test coverage: Gaps — no tests for partial data corruption

**EventSource Reconnection - Unbounded Retry:**

- Files: `frontend/src/lib/usePriceStream.ts` (lines 31-33)
- Why fragile: EventSource's built-in retry uses exponential backoff with no documented maximum. If the server is down for hours, the browser will keep retrying and accumulate pending requests
- Safe modification: Detect repeated reconnection failures and show a "Connection lost — please refresh" message to the user. Add a maximum backoff cap
- Test coverage: Gaps — no tests for sustained disconnection

---

## Scaling Limits

**SQLite Concurrency Ceiling:**

- Current capacity: SQLite can handle ~10-20 concurrent write operations comfortably. Read operations scale better
- Limit: Beyond ~50 concurrent users on a shared SQLite database, contention will cause timeouts and performance degradation
- Scaling path: Migrate to PostgreSQL or another multi-user database for true concurrency. Implement connection pooling with `sqlalchemy`

**Market Data Polling Throughput - Massive API:**

- Current capacity: Free tier = 5 requests/minute (one every 12 seconds). Paid tiers up to 5/second
- Limit: With 10 tickers at 5 req/min, refresh rate is ~12 seconds per full watchlist. This is acceptable for retail but slow for trading
- Scaling path: Upgrade to a higher-tier Massive plan, or switch to WebSocket-based market data (requires API change)

**SSE Stream Payload Size:**

- Current capacity: Watchlist of 10 tickers generates ~500 bytes per 500ms tick (~1KB/sec per client)
- Limit: 100 concurrent clients = ~100KB/sec outbound traffic
- Scaling path: Implement per-client subscription filtering (noted in Performance section). Compress SSE payloads with gzip

**Frontend State Management:**

- Current capacity: Stores chat history in React state (no persistence). Chat message history grows unbounded
- Limit: ~1000 messages → noticeable lag in rendering and scrolling
- Scaling path: Implement windowing/virtualization in the chat panel. Persist chat to `localStorage` or IndexedDB. Implement pagination

---

## Dependencies at Risk

**LiteLLM Version Constraints:**

- Risk: `litellm>=1.101.0` in `backend/pyproject.toml` is a lower bound with no upper bound. Major version updates could break the API
- Impact: `pip install` could pull `litellm 2.x` with breaking changes to the `completion()` function signature
- Migration plan: Pin to a specific minor version (e.g., `litellm>=1.101.0,<1.200.0`) and test upgrades before rolling out

**Next.js Version Mismatch in Tests:**

- Risk: `frontend/package.json` specifies `next 16.3.5`, but the Playwright tests may be running against an older Node version if not kept in sync
- Impact: Build-time incompatibilities or runtime feature gaps
- Migration plan: Lock Node version in `.nvmrc` to match CI/CD. Pin all major dependencies to specific versions in production

**Package Typo in Development Dependencies:**

- Risk: `backend/pyproject.toml` has `httpx2>=2.13.0` which is not a real package (should be `httpx`)
- Impact: `pip install -e .[dev]` will fail when attempting to install dev dependencies for testing
- Migration plan: Correct the typo immediately to `httpx>=2.13.0`. This doesn't affect production builds (httpx is not in the main dependencies)

**Pydantic Version Constraints:**

- Risk: `pydantic>=2.13.5` spans a wide range. Pydantic 3.x (when released) could have breaking changes
- Impact: Future upgrades may require code changes
- Migration plan: Monitor Pydantic releases. Pin to `>=2.13.5,<3.0.0` once Pydantic 3 is released

---

## Missing Critical Features

**No Error Recovery for LLM Service Outage:**

- Problem: If the LLM service (OpenRouter) is down, all chat operations fail. There's no graceful degradation or queuing
- Blocks: Users cannot interact with the AI during service outages
- Suggested approach: Implement a local fallback LLM (smaller open-source model) or queue chat messages and retry with exponential backoff

**No Price History API Endpoint:**

- Problem: Sparklines in the watchlist are built from SSE data accumulated since page load. On refresh, the history is lost
- Blocks: Sparklines reset on every page refresh, losing any historical context
- Suggested approach: Add `GET /api/prices/{ticker}/history?minutes=60` endpoint that returns a time-series of prices from the database or a caching layer

**No Portfolio Export or Reporting:**

- Problem: Users cannot export their portfolio or trade history for record-keeping or analysis
- Blocks: Compliance and personal financial record-keeping
- Suggested approach: Add endpoints for CSV/JSON export of positions and trade history

**No Undo/Rollback for Trades:**

- Problem: Trades are executed immediately with no undo. User mistakes can't be corrected
- Blocks: Accidental trades result in lost simulated money
- Suggested approach: Implement a 10-second grace period with a "Undo" button before trades are finalized

---

## Test Coverage Gaps

**Frontend Component Tests - Critical Components Untested:**

- What's not tested: `Header`, `MainChart`, `PriceChart`, `PortfolioHeatmap`, `PnlChart`, `TradeBar` (partially)
- Files: Missing test files in `frontend/src/components/__tests__/`
- Risk: Changes to these components could break critical UI functionality unnoticed
- Priority: **High** — These are core visuals of the trading workstation

**Frontend Hooks - No Tests:**

- What's not tested: `usePriceStream` hook (price accumulation, reconnection logic, connection state)
- Files: `frontend/src/lib/usePriceStream.ts` (no test file)
- Risk: SSE reconnection logic could silently break, leaving users with stale prices
- Priority: **High** — The hook is critical to the real-time experience

**LLM Error Cases - Not Tested:**

- What's not tested: LLM service timeout, malformed responses, rate limiting, network errors
- Files: `backend/llm/client.py` (test_llm_mock.py exists but only tests the mock, not real error paths)
- Risk: Production LLM failures won't be caught
- Priority: **High** — LLM failures are common in production

**Massive API Error Responses - Not Tested:**

- What's not tested: JSON parsing errors, rate limit headers, 5xx responses, malformed snapshots
- Files: `backend/market/massive.py` (test_market_massive.py has happy-path tests)
- Risk: Edge cases in the Massive integration could crash the backend
- Priority: **Medium** — Covered by happy-path tests; edge cases rare but dangerous

**Database Corruption Scenarios - Not Tested:**

- What's not tested: Partial transaction failures, concurrent write conflicts, orphaned data
- Files: No tests for edge cases in `backend/db/`
- Risk: Silent data corruption could result in incorrect portfolio calculations
- Priority: **Medium** — Concurrent writes are rare due to single-user design, but still a risk

**Frontend Network Resilience - Not Tested:**

- What's not tested: Handling of network timeouts, 5xx errors from backend, connection dropouts during trades
- Files: `frontend/src/lib/api.ts` (no retry logic or timeout handling)
- Risk: Network hiccups could leave the UI in an inconsistent state
- Priority: **Medium** — Especially important for a trading application

**E2E Tests - Limited Scope:**

- What's not tested: Error flows (failed trades, LLM errors, network failures), edge cases (selling more than owned, insufficient cash), concurrent operations
- Files: `test/e2e/finally.spec.ts` (only 1 spec file with happy-path scenarios)
- Risk: Critical error paths are untested in integration
- Priority: **Medium** — Happy path is covered, but error handling is not

---

*Concerns audit: 2026-09-20*
