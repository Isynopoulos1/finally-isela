---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# Coding Conventions

**Analysis Date:** 2026-09-20

## Naming Patterns

### TypeScript/Frontend Files

**Files:**

- Components: PascalCase (e.g., `Watchlist.tsx`, `TradeBar.tsx`, `WatchlistRow.tsx`)
- Utilities/Hooks: camelCase (e.g., `usePriceStream.ts`, `api.ts`, `types.ts`, `format.ts`)
- Test files: Match source file name with `.test.tsx` suffix (e.g., `Watchlist.test.tsx`)
- Directories: kebab-case for feature directories, `__tests__` for test colocations

**Functions:**

- React components: PascalCase, exported as named exports (e.g., `export function Watchlist(...)`)
- Custom hooks: `use` prefix + PascalCase (e.g., `usePriceStream()`)
- Event handlers: `handle` + event name in camelCase (e.g., `handleAdd`, `handleSelect`)
- Regular functions: camelCase (e.g., `waitForLivePrice()`)
- API methods: camelCase, object-organized (e.g., `api.getWatchlist()`, `api.addTicker()`)

**Variables:**

- State variables: camelCase (e.g., `ticker`, `quantity`, `pending`, `priceHistory`)
- Type/interface variable names: PascalCase (e.g., `WatchlistItem`, `Position`)
- Constants: camelCase or UPPER_SNAKE_CASE depending on context
  - `MAX_HISTORY_PER_TICKER = 240` — module-level constant
  - `API_BASE` — configuration constant

**Types:**

- Use `interface` keyword (not `type`) for object shapes (e.g., `interface WatchlistProps { ... }`)
- Use `type` for unions and literals (e.g., `type TradeSide = "buy" | "sell"`)
- Import types with `import type { ... }` for tree-shaking
- Suffix component prop interfaces with `Props` (e.g., `WatchlistProps`, `TradeBarProps`)

### Python/Backend Files

**Files:**

- Modules: snake_case (e.g., `simulator.py`, `schema.py`, `trading.py`)
- Package directories: snake_case (e.g., `market/`, `portfolio/`, `api/`, `db/`, `llm/`)
- Test files: `test_` prefix + module name (e.g., `test_market_simulator.py`, `test_db_schema.py`)

**Functions:**

- Functions: snake_case (e.g., `execute_trade()`, `build_portfolio_context()`, `normalize()`)
- Private functions: `_` prefix (e.g., `_table_names()`, `_correlation()`)
- Async functions: same snake_case convention (e.g., `async def start()`)

**Classes:**

- Classes: PascalCase (e.g., `TradeError`, `ChatCompletion`, `SimulatorProvider`)
- Exception classes: Inherit from `Exception` with `Error` suffix (e.g., `class TradeError(Exception)`)
- Pydantic models: PascalCase (e.g., `ChatCompletion`, `ChatTrade`, `WatchlistChange`)

**Variables:**

- Function/module-level: snake_case (e.g., `ticker`, `quantity`, `cash_balance`)
- Constants: UPPER_SNAKE_CASE (e.g., `MIN_QUANTITY = 1e-9`, `ANNUAL_VOL`)
- Logger: `log = logging.getLogger(__name__)`

## Code Style

### Formatting

**Frontend (TypeScript/React):**

- No `.prettierrc` configured; relies on ESLint for style enforcement
- ESLint config: `eslint.config.mjs` (flat config format, ESLint v9+)
- Extends: `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`
- Indentation: 2 spaces (inferred from codebase)
- Line length: Implied ~80-100 characters (no explicit config)
- Semicolons: Required (ESLint default)

**Backend (Python):**

- Ruff for linting and formatting
- Configuration in `pyproject.toml`:
  - Line length: 100
  - Target Python: 3.12+

### Linting

**Frontend:**

- Tool: ESLint 9 (flat config)
- Config file: `frontend/eslint.config.mjs`
- Enforces Next.js best practices, TypeScript strict mode
- Ignores: `.next/`, `out/`, `build/`, `next-env.d.ts`

**Backend:**

- Tool: Ruff
- Config in `backend/pyproject.toml`
- Manages both style and linting together

## Import Organization

### Frontend

**Order:**

1. React and Next.js imports (`import { useState } from "react"`)
2. External dependencies (`import { render, screen } from "@testing-library/react"`)
3. Internal absolute imports using `@/` alias (`import { Watchlist } from "@/components/..."`)
4. Type imports grouped separately (`import type { ... } from "@/lib/types"`)

**Path Aliases:**

- `@/*` → `./src/*` (configured in `tsconfig.json`)
- All internal imports use `@/` for clarity and IDE support

**Example from `Watchlist.tsx`:**

```typescript
"use client";

import { useState, type FormEvent } from "react";
import { WatchlistRow } from "./WatchlistRow";
import type { PriceTick, WatchlistItem } from "@/lib/types";
```

### Backend

**Order:**

1. Standard library imports (`import sqlite3`, `from pathlib import Path`)
2. Third-party imports (`from fastapi import FastAPI`, `from pydantic import BaseModel`)
3. Local/relative imports (`from db import repository`, `from market.factory import make_provider`)
4. Use absolute imports from package root (no relative `..` imports where possible)

**Example from `portfolio/trading.py`:**

```python
from db import repository
from market.interface import PriceUpdate
from market.tickers import normalize
from portfolio.context import build_portfolio_context
```

## Error Handling

### Frontend

**Pattern: Try-catch with user-friendly messages:**

```typescript
try {
  await onAdd(ticker);
  setDraft("");
  setError(null);
} catch {
  setError(`Couldn't add ${ticker}`);
}
```

**Guidelines:**

- Catch all errors as `catch (err)` or `catch (err instanceof Error ? err.message : "...")`
- Display user-friendly error messages in state (e.g., `error` state rendered as `<p className="text-down">{error}</p>`)
- Clear errors on successful operations (`setError(null)`)
- For network errors, show the fetch error message directly or a generic fallback

**API error handling in `lib/api.ts`:**

```typescript
if (!res.ok) {
  const body = await res.text().catch(() => "");
  throw new Error(`${init?.method ?? "GET"} ${path} failed (${res.status}): ${body}`);
}
```

### Backend

**Pattern: Custom exception classes for domain errors:**

```python
class TradeError(Exception):
    """Validation failure. Message is safe to show directly to the user."""
```

**Guidelines:**

- Define domain-specific exception classes (e.g., `TradeError`) that inherit from `Exception`
- Include docstring explaining when the error is raised
- Catch and convert to HTTP responses in API routes:
  ```python
  try:
      return execute_trade(...)
  except TradeError as exc:
      raise HTTPException(status_code=400, detail=str(exc)) from exc
  ```
- Messages in `TradeError` are designed to be safe to show to users
- Use `raise ... from exc` for exception chaining to preserve tracebacks

**Validation errors:**

- Pydantic models handle request validation automatically via `BaseModel`
- Invalid side, quantity, or missing fields raise `ValidationError` → 422 response automatically

## Logging

### Frontend

**Framework:** `console` object (native browser logging)

**Patterns:**

- Minimal console output; use in development only via conditional logging
- No structured logging library used
- Most state is tracked via React state, not logs

### Backend

**Framework:** Python's built-in `logging` module

**Patterns:**

- Each module creates a logger: `log = logging.getLogger(__name__)`
- Used in market data providers (`market/simulator.py`, `market/massive.py`, `market/factory.py`)
- Log messages for informational events (e.g., provider startup/shutdown)
- No structured logging format configured; uses default format

**Example from `market/factory.py`:**

```python
import logging
log = logging.getLogger(__name__)
```

## Comments

### When to Comment

- **Module docstrings:** Required for all `.py` files. Explain module purpose.
  ```python
  """Portfolio endpoints: view holdings, execute trades, view value history."""
  ```
- **Function docstrings:** Optional but recommended for complex logic.
  ```python
  """Validate and execute a market order, then return the updated portfolio context.
  
  `prices` is the market provider's current price cache.
  Raises `TradeError` on any validation failure.
  """
  ```
- **Inline comments:** Rare. Only for non-obvious logic or important invariants.

### JSDoc/TSDoc

- **Not used** in this codebase. TypeScript interfaces and type annotations are sufficient.
- Function signatures are clear enough that docstrings are rarely needed.

## Function Design

### Size

**Frontend:**

- React components: 20-100 lines typical. Extracted smaller pieces as separate components if logic grows.
- Custom hooks: 20-40 lines. State and side effects clearly isolated.
- Utility functions: Short, single-purpose (e.g., `request<T>(...)` for API calls, ~20 lines)

**Backend:**

- Functions: 10-50 lines typical. Multi-step processes broken into smaller functions.
- Example: `execute_trade()` is ~50 lines covering buy/sell branches

### Parameters

**Frontend:**

- React components: Props passed as a destructured object (`{ items, priceHistory, selectedTicker, ... }`)
- Functions: Use object params for 3+ arguments (e.g., API request options)
  ```typescript
  async function request<T>(path: string, init?: RequestInit): Promise<T>
  ```

**Backend:**

- Functions: Named parameters with type hints
  ```python
  def execute_trade(ticker: str, side: str, quantity: float, prices: dict[str, PriceUpdate])
  ```
- Avoid excessive parameter nesting; use Pydantic models for complex inputs

### Return Values

**Frontend:**

- React components: Return JSX (no explicit return type in function signature, let TypeScript infer)
- Functions: Use explicit return types
  ```typescript
  export const api = {
    getWatchlist: () => request<WatchlistItem[]>("/api/watchlist"),
  };
  ```

**Backend:**

- Functions: Include return type in signature
  ```python
  def execute_trade(...) -> dict:
  ```
- Async functions: Return type is wrapped in coroutine, but signature shows unwrapped type
  ```python
  async def get_portfolio(request: Request) -> dict:
  ```

## Module Design

### Exports

**Frontend:**

- Named exports preferred (`export function Watchlist(...) { }`)
- Default exports avoided (helps with tree-shaking and clarity)
- Index files (`index.ts`) used rarely; direct imports preferred

**Backend:**

- Functions and classes exported at module level for import
- `__init__.py` files minimal (often empty)
- Public API exposed via `from module import function`

### Barrel Files

**Frontend:**

- Not used. Each component imported directly from its file.
  ```typescript
  import { Watchlist } from "@/components/Watchlist";
  import { TradeBar } from "@/components/TradeBar";
  ```

**Backend:**

- Not used in this codebase. Direct imports from modules.

## TypeScript Configuration

**Key settings in `tsconfig.json`:**

- `"strict": true` — Strict type checking enabled
- `"jsx": "react-jsx"` — JSX handled by React 18+ transform
- `"moduleResolution": "bundler"` — Next.js bundler resolution
- `"skipLibCheck": true` — Skip checking .d.ts files for performance
- `"resolveJsonModule": true` — JSON imports allowed
- Path aliases: `"@/*": ["./src/*"]`

**Implications:**

- All values must be typed
- `null` and `undefined` are distinct (no implicit union)
- Function parameters must have types
- Improves IDE support and catches bugs at compile time

---

*Convention analysis: 2026-09-20*
