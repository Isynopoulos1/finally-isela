---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# Testing Patterns

**Analysis Date:** 2026-09-20

## Test Framework

### Frontend (Unit Tests)

**Runner:**

- Vitest 5.0.1 (lightweight alternative to Jest)
- Config: `frontend/vitest.config.mts`
- Environment: jsdom (browser API simulation)

**Assertion Library:**

- Vitest built-in assertions (`expect()`)
- React Testing Library (`@testing-library/react`) for DOM testing
- `@testing-library/jest-dom/vitest` for extended matchers (via `vitest.setup.ts`)

**Run Commands:**

```bash
npm test                    # Run all tests once
npm run test -- --watch    # Watch mode (if configured)
npm run test -- --coverage # Coverage report (if configured)
```

### Backend (Unit & Integration Tests)

**Runner:**

- pytest 8.0+
- Config: `pyproject.toml` (`[tool.pytest.ini_options]`)
  - `asyncio_mode = "auto"` — automatically handles async fixtures
  - `testpaths = ["tests"]` — looks for tests in `backend/tests/`

**Async Support:**

- pytest-asyncio 0.24+ for async test functions
- Automatic detection of async fixtures and test functions

**Run Commands:**

```bash
cd backend
uv run pytest              # Run all tests
uv run pytest -v          # Verbose output
uv run pytest -k <name>   # Run specific test by name
uv run pytest --tb=short  # Shorter traceback format
```

### E2E Tests

**Framework:**

- Playwright (@playwright/test)
- Config: `test/e2e/finally.spec.ts` (inline configuration in test file)
- Execution: Serial (one test at a time, shared state)

**Run Commands:**

```bash

# Requires Docker container running

npm run test:e2e          # Run E2E suite
npm run test:e2e -- --headed  # Browser visible
```

## Test File Organization

### Frontend

**Location:**

- Colocated in `__tests__` directory next to components
- Example: `src/components/Watchlist.tsx` → `src/components/__tests__/Watchlist.test.tsx`

**Naming:**

- `{ComponentName}.test.tsx` for component tests
- One test file per component

**Structure:**

```
frontend/src/
├── components/
│   ├── Watchlist.tsx
│   ├── TradeBar.tsx
│   ├── ChatPanel.tsx
│   └── __tests__/
│       ├── Watchlist.test.tsx
│       ├── TradeBar.test.tsx
│       └── ChatPanel.test.tsx
├── lib/
│   └── api.ts          # Tested via E2E or integration tests
└── app/
    └── page.tsx        # Tested via E2E tests
```

### Backend

**Location:**

- `backend/tests/` directory (separate from source)
- Organized by domain: `test_db_*.py`, `test_api_*.py`, `test_market_*.py`, `test_llm_*.py`

**Naming:**

- `test_*.py` prefix for all test files
- Example: `test_market_simulator.py`, `test_api_watchlist.py`

**Structure:**

```
backend/
├── market/
│   ├── simulator.py
│   └── factory.py
├── api/
│   ├── portfolio.py
│   ├── chat.py
│   └── watchlist.py
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── test_market_simulator.py
    ├── test_market_massive.py
    ├── test_api_health.py
    ├── test_api_watchlist.py
    ├── test_api_portfolio.py
    ├── test_api_chat.py
    ├── test_db_schema.py
    ├── test_db_connection.py
    ├── test_llm_schema.py
    └── test_llm_mock.py
```

### E2E Tests

**Location:**

- `test/e2e/` directory
- Separate from frontend/backend unit tests

**Naming:**

- `{feature}.spec.ts` (e.g., `finally.spec.ts` for main workflows)

**Structure:**

```
test/
└── e2e/
    └── finally.spec.ts          # All scenarios in one suite (serial mode)
```

## Test Structure

### Frontend: Component Test Pattern

```typescript
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Watchlist } from "../Watchlist";

// Mock dependencies if needed
vi.mock("../PriceChart", () => ({
  PriceChart: () => <div data-testid="chart-stub" />,
}));

describe("Watchlist add/remove", () => {
  it("submits a trimmed, uppercased ticker and clears the input", async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn().mockResolvedValue(undefined);

    render(
      <Watchlist
        items={[]}
        priceHistory={{}}
        selectedTicker={null}
        onSelect={() => {}}
        onAdd={onAdd}
        onRemove={vi.fn()}
      />,
    );

    const input = screen.getByLabelText("Add ticker");
    await user.type(input, "  pypl ");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(onAdd).toHaveBeenCalledWith("PYPL");
  });
});
```

**Structure:**

1. Imports (React Testing Library, vitest, component under test)
2. Mocks (if needed via `vi.mock()`)
3. `describe()` block grouping related tests
4. Individual `it()` tests with:
   - Arrange: `render()` component with props
   - Act: `await user.type()`, `await user.click()`, etc.
   - Assert: `expect().toHaveBeenCalledWith()`, `expect(element).toHaveText()`, etc.

**Patterns:**

- Use `userEvent` for realistic user interactions (not `fireEvent`)
- Mock callback props with `vi.fn()` for testing component behavior
- Use `data-testid`, `aria-label`, or `getByRole` for element selection
- `await user.setup()` before interactions to handle async state changes

### Backend: Test Pattern

```python
import pytest
from db.schema import init_db

TABLES = {"users_profile", "watchlist", "positions", ...}

def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row["name"] for row in rows}

def test_init_db_creates_all_tables():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    assert TABLES <= _table_names(conn)

def test_init_db_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    init_db(conn)  # must not raise
    assert TABLES <= _table_names(conn)
```

**Structure:**

1. Imports
2. Helper functions (e.g., `_table_names()`) prefixed with `_`
3. Test functions with `test_` prefix
4. Arrange: create fixtures/state
5. Act: call function under test
6. Assert: `assert` statements

**Patterns:**

- Simple `assert` statements for clarity
- Use fixtures from `conftest.py` by adding them as function parameters
- No explicit setup/teardown; fixtures handle lifecycle via `yield`
- Helper functions private (prefixed with `_`) not exposed as tests

### E2E: Playwright Test Pattern

```typescript
test.describe.configure({ mode: "serial" });

async function waitForLivePrice(page: Page, ticker: string) {
  const row = page.getByTestId(`watchlist-row-${ticker}`);
  await expect(row).toBeVisible();
  await expect(row.locator("span").nth(1)).not.toHaveText("—", { timeout: 10_000 });
}

test.describe("FinAlly E2E", () => {
  test("fresh start: default watchlist, $10k cash, live prices", async ({ page }) => {
    await page.goto("/");

    for (const ticker of DEFAULT_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }

    await expect(page.getByTestId("cash-balance")).toHaveText("$10,000.00");
    await expect(page.getByTestId("portfolio-total-value")).toHaveText("$10,000.00");

    await waitForLivePrice(page, "AAPL");
    await expect(page.getByTestId("connection-status")).toHaveAttribute("aria-label", "Live");
  });

  test("add and remove a ticker from the watchlist", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Add ticker").fill("DIS");
    await page.getByRole("button", { name: "Add" }).click();
    await expect(page.getByTestId("watchlist-row-DIS")).toBeVisible();

    await page.getByLabel("Remove DIS from watchlist").click();
    await expect(page.getByTestId("watchlist-row-DIS")).toHaveCount(0);
  });
});
```

**Structure:**

1. `test.describe.configure({ mode: "serial" })` — run tests sequentially, share state
2. Helper async functions (e.g., `waitForLivePrice()`) for reusable flows
3. `test.describe()` groups related scenarios
4. Each `test()` is one user workflow (can depend on previous tests in serial mode)
5. Playwright assertions with `await expect()`

**Patterns:**

- Tests run in order; earlier tests set up state for later tests
- Selectors: `getByTestId()`, `getByLabel()`, `getByRole()` for clarity and resilience
- Use `await expect(...).toBeVisible()` for async conditions
- `await page.goto("/")` at start of most tests (idempotent)
- Use `await expect().poll()` to retry assertions with timeout

## Mocking

### Frontend: Mocking Dependencies

**Framework:** Vitest's `vi.mock()` (same API as Jest)

**Pattern for mocking a child component:**

```typescript
vi.mock("../PriceChart", () => ({
  PriceChart: () => <div data-testid="chart-stub" />,
}));
```

**Pattern for mocking module functions:**

```typescript
const mockCallLlm = vi.fn().mockResolvedValue({
  message: "Buying 1 share.",
  trades: [{ ticker: "AAPL", side: "buy", quantity: 1 }],
});
vi.mocked(api.callLlm).mockImplementation(() => Promise.resolve(mockCallLlm));
```

**What to Mock:**

- Child components (especially charting, heavy rendering)
- API calls (for unit tests; integration tests call real API via `api_client` fixture)
- External services (e.g., EventSource for SSE)

**What NOT to Mock:**

- Core React hooks (`useState`, `useEffect`) — use real state
- User input mechanisms (`@testing-library/user-event`) — test realistic interactions
- DOM structure — test actual rendered output

### Backend: Mocking External Calls

**Framework:** `unittest.mock.Mock` (Python standard library)

**Pattern for mocking LLM calls:**

```python
@pytest.fixture
def mock_llm(monkeypatch):
    """Replace the real LLM call with a controllable mock."""
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    mocked = Mock()
    monkeypatch.setattr("api.chat.call_llm", mocked)
    return mocked

def test_chat_executes_valid_trade(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Buying 1 share of AAPL for you.",
        trades=[ChatTrade(ticker="AAPL", side="buy", quantity=1)],
    )
    response = api_client.post("/api/chat", json={"message": "buy 1 AAPL"})
    assert response.status_code == 200
```

**Pattern for mocking environment variables:**

```python
def test_llm_mock_mode(api_client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    response = api_client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 200
```

**What to Mock:**

- External API calls (LLM, market data provider)
- Environment variables in tests
- Randomness (e.g., `random.gauss()` in market simulator tests — pin to fixed value)

**What NOT to Mock:**

- Database operations (use real in-memory DB via fixtures)
- Core business logic (execute_trade, price calculations)
- HTTP status codes (let FastAPI handle validation)

## Fixtures and Factories

### Frontend: Test Setup

**No fixture library used.** Setup inline or via helper functions:

```typescript
const onAdd = vi.fn().mockResolvedValue(undefined);
render(
  <Watchlist
    items={[]}
    priceHistory={{}}
    selectedTicker={null}
    onSelect={() => {}}
    onAdd={onAdd}
    onRemove={vi.fn()}
  />,
);
```

### Backend: Test Fixtures

**Location:** `backend/tests/conftest.py`

**Fixture: `db_conn` — Fresh temporary database**

```python
@pytest.fixture
def db_conn(tmp_path):
    """Point the shared DB connection at a fresh temp file for one test."""
    conn = connection.get_connection(tmp_path / "test.db")
    yield conn
    connection.close_connection()
```

**Fixture: `api_client` — FastAPI test client with temp DB**

```python
@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """A TestClient wired to a fresh temp DB and the simulator provider."""
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    connection.get_connection(tmp_path / "test.db")
    from main import app
    with TestClient(app) as client:
        yield client
    connection.close_connection()
```

- Wipes `MASSIVE_API_KEY` to force simulator (not real API)
- Database auto-initializes on first request
- Returns a TestClient for HTTP calls (`api_client.post()`, `api_client.get()`)

**Fixture: `live_server` — Real HTTP server for SSE testing**

```python
@pytest.fixture
def live_server(tmp_path, monkeypatch):
    """Run the real app on a real socket for SSE testing.
    
    TestClient buffers entire response before returning; can't observe a 
    never-ending SSE stream. A real socket works like production.
    """
    # ... spins up uvicorn server on random port, yields URL
    yield f"http://127.0.0.1:{port}"
    # ... tears down server
```

**Usage in tests:**

```python
def test_llm_mock_mode_is_deterministic_and_skips_network(api_client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    response = api_client.post("/api/chat", json={"message": "hello there"})
    assert response.status_code == 200

def test_sse_stream_is_live(live_server):
    # Use live_server URL for real HTTP connections
```

**Fixture lifetime:**

- Fixtures with `yield` run teardown code after the test
- Database fixtures ensure fresh state per test
- `api_client` handles app initialization/cleanup automatically

## Coverage

**Requirements:** Not enforced (no minimum coverage target configured)

**View Coverage (if configured):**

```bash

# Frontend (if script exists)

npm test -- --coverage

# Backend

uv run pytest --cov=. --cov-report=html

# Then open htmlcov/index.html

```

**Current state:** Coverage measurement not configured in this project. Tests are focused on critical paths:

- Frontend: component behavior, user interactions
- Backend: data validation, trade logic, API contracts
- E2E: end-to-end workflows (fresh start, buy/sell, chat)

## Test Types

### Unit Tests — Frontend Components

**Scope:** Individual React component behavior in isolation

**Approach:**

- Render component with mock props and callbacks
- Simulate user interactions (`userEvent`)
- Assert component behavior (state changes, callback calls)

**Example:** `Watchlist.test.tsx`

- Tests adding a ticker (trimming, uppercasing, callback invocation)
- Tests removing a ticker (callback invocation, no selection)
- Mocks child components (PriceChart)

### Unit Tests — Backend Functions

**Scope:** Individual functions/modules (trade logic, schema validation, calculations)

**Approach:**

- Call function with known inputs
- Use in-memory database or no database
- Assert return values and side effects

**Examples:**

- `test_gbm_keeps_prices_positive()` — math correctness
- `test_parses_full_valid_schema()` — Pydantic validation
- `test_execute_trade_buys_shares()` — business logic

### Integration Tests — Backend API

**Scope:** Full API route end-to-end (request → response)

**Approach:**

- Use `api_client` fixture (TestClient + real app + real DB)
- Send HTTP requests, inspect responses
- Verify database state changes

**Examples:**

- `test_llm_mock_mode_buy_trigger_phrase_executes_trade()` — POST /chat, verify portfolio updated
- `test_add_ticker()` — POST /watchlist, verify list returned
- `test_chat_executes_valid_trade()` — POST /chat with mocked LLM, verify trade executed

### E2E Tests — Full Workflow

**Scope:** User scenarios from page load to completion

**Approach:**

- Browser automation via Playwright
- Real app + real database (Docker container)
- Multiple tests in serial, sharing state

**Examples:**

- Fresh start: Load page → verify default watchlist, $10k, live prices
- Buy workflow: Enter ticker/quantity → click Buy → verify position, cash decreased
- Chat workflow: Send message → verify response, trades executed inline

**Constraints:** Tests run serially (`mode: "serial"`) because:

- Single shared database (single-user app)
- Each test's state is a precondition for the next
- Parallel execution would corrupt shared state

## Common Patterns

### Async Testing — Frontend

```typescript
it("submits on user interaction", async () => {
  const user = userEvent.setup();
  const onAdd = vi.fn().mockResolvedValue(undefined);
  
  render(<Watchlist onAdd={onAdd} ... />);
  
  const input = screen.getByLabelText("Add ticker");
  await user.type(input, "AAPL");
  await user.click(screen.getByRole("button", { name: "Add" }));
  
  expect(onAdd).toHaveBeenCalledWith("AAPL");
});
```

**Patterns:**

- Always `await user.type()` and `await user.click()` (userEvent is async)
- Use `await expect()` for assertions on async component updates
- Mock async callbacks with `.mockResolvedValue()` or `.mockRejectedValue()`

### Async Testing — Backend

```python
@pytest.mark.asyncio
async def test_stream_yields_price_ticks(live_server):
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"{live_server}/api/stream/prices") as resp:
            # Read a few events from the live SSE stream
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    tick = json.loads(line[5:])
                    assert "ticker" in tick
                    assert "price" in tick
                    break
```

**Patterns:**

- Use `pytest-asyncio` to mark async test functions
- Use `httpx.AsyncClient` for real HTTP (SSE requires real connection)
- Fixtures auto-detect async (via `asyncio_mode = "auto"` in config)

### Error Testing — Frontend

```typescript
it("displays error message on failure", async () => {
  const user = userEvent.setup();
  const onAdd = vi.fn().mockRejectedValue(new Error("Duplicate ticker"));
  
  render(<Watchlist onAdd={onAdd} ... />);
  
  const input = screen.getByLabelText("Add ticker");
  await user.type(input, "AAPL");
  await user.click(screen.getByRole("button", { name: "Add" }));
  
  await expect(screen.getByText(/Couldn't add/)).toBeInTheDocument();
});
```

### Error Testing — Backend

```python
def test_chat_reports_failed_trade_without_crashing(api_client, mock_llm):
    mock_llm.return_value = ChatCompletion(
        message="Attempting to buy.",
        trades=[ChatTrade(ticker="AAPL", side="buy", quantity=1_000_000)],
    )
    
    response = api_client.post("/api/chat", json={"message": "buy a lot"})
    assert response.status_code == 200  # Doesn't crash
    body = response.json()
    assert body["trades"][0]["status"] == "failed"
    assert "Insufficient cash" in body["trades"][0]["error"]
```

**Patterns:**

- Catch exceptions and report errors in response (don't let them crash API)
- Status code remains 200 (validation error, not server error)
- Error details included in response payload

---

*Testing analysis: 2026-09-20*
