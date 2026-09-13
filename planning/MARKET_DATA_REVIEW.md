# Market Data Backend — Code Review

**Reviewer:** Claude Sonnet 4.6  
**Date:** 2026-09-13  
**Branch reviewed:** `upstream/market-data-demo` (commit `5594a85`)  
**Scope:** `backend/app/market/` (8 source files) + `backend/tests/market/` (6 test files)

---

## 1. Test Results

**Tests could not be run locally.** No Python 3.12 or `uv` is installed in the current environment.

**Prior review results (from `planning/archive/MARKET_DATA_REVIEW.md`, run on `upstream/market-data-review` commit):**
- 73 tests collected
- 68 passed, 5 failed
- All 5 failures were in `test_massive.py` due to missing `massive` package + lazy-import patching issues
- Not logic bugs — resolved in the subsequent fix commit (`f89aa14 Fix all issues from market data code review`)

The fix commit applied 10 file changes. Per the `MARKET_DATA_SUMMARY.md`, all 7 review issues were resolved and all 73 tests pass in the final state. Coverage: **84% overall** (models 100%, cache 100%, factory 100%, simulator 98%, massive_client 56% expected, stream 31% expected).

---

## 2. Architecture Assessment

The implementation follows a clean strategy pattern:

```
MarketDataSource (ABC)
├── SimulatorDataSource  →  GBM + Cholesky-correlated moves
└── MassiveDataSource    →  Polygon.io REST poller
        │
        ▼
   PriceCache (thread-safe, version-stamped)
        │
        └──→ SSE endpoint (/api/stream/prices)
```

**What works well:**

- `PriceCache` is the correct single point of truth. Thread-safe (threading.Lock), necessary since `MassiveDataSource._fetch_snapshots` runs in `asyncio.to_thread`.
- `PriceUpdate` is `frozen=True, slots=True` — immutable and memory-efficient.
- GBM math is correct: `S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)`. The Cholesky decomposition for correlated moves is the mathematically proper approach, and per-ticker parameters (TSLA σ=0.50 vs V σ=0.17) reflect real-world volatility differences.
- Cache is pre-seeded before the background task loop starts, so the SSE endpoint has data on the first request.
- Both background tasks handle cancellation and exception resilience correctly.
- The factory pattern is clean: reads `MASSIVE_API_KEY`, returns an unstarted source.

---

## 3. Conformance to Design Documents

The implementation deviates from `MARKET_DATA_DESIGN.md` in several areas. Most deviations are improvements; two are gaps.

### Intentional improvements

| Design | Implementation | Assessment |
|--------|---------------|------------|
| `update_tickers(list)` replaces the whole set | `add_ticker` / `remove_ticker` for granular changes | Better API — avoids a full diff on every watchlist change |
| Uniform `ANNUAL_VOL = 0.30` for all tickers | Per-ticker `sigma` in `seed_prices.py` | More realistic; TSLA should not move like JPM |
| Simple market-factor correlation (ρ shared draw) | Full Cholesky decomposition with sector groups | Mathematically correct; the design doc's factor model was an approximation |
| `change_pct` stored on `PriceUpdate` | Computed properties `change`, `change_percent`, `direction` | Cleaner — derived values should not be stored |

### Design gaps

**1. No price history endpoint.**  
`GET /api/prices/{ticker}/history` (the rolling 30-minute buffer from `MARKET_DATA_DESIGN.md §7`) is not implemented. The main chart has no REST data source. Sparklines can accumulate from SSE, but the large chart area will be empty on first load and after refresh. This is the most significant missing piece.

**2. No ticker normalization layer.**  
`MARKET_DATA_DESIGN.md §3` specifies `normalize()` / `normalize_all()` helpers applied at every entry point. `MassiveDataSource.add_ticker` normalizes to uppercase; `SimulatorDataSource.add_ticker` does not. A lowercase ticker passed to the simulator will be tracked as-is, creating a cache/API mismatch.

**3. SSE sends full snapshot on every version tick, not deltas.**  
The design doc specifies delta protocol: full snapshot on connect, then only changed tickers. The current implementation emits all prices whenever `cache.version` increments. For the simulator (all tickers step simultaneously) this makes no practical difference. For Massive (15-second polls, sparse updates) it is inefficient but not broken.

**4. No `tracked_tickers` utility.**  
`MARKET_DATA_DESIGN.md §8.2` calls for `tracked_tickers = watchlist ∪ open_positions`. This logic is not in the market layer — it belongs in the application wiring that hasn't been built yet. The market layer provides the primitives; the application layer needs to call `add_ticker` / `remove_ticker` correctly.

---

## 4. Specific Issues

### Fixed issues (resolved in `f89aa14`)

The prior review found 7 issues. All were fixed:

1. ✅ `pyproject.toml` missing `packages = ["app"]` in build config
2. ✅ Massive tests fragile when `massive` package absent — imports moved to module level
3. ✅ `_generate_events` return type annotation (`-> None` → `-> AsyncGenerator[str, None]`)
4. ✅ Unused test imports (`pytest`, `math`, `asyncio`)
5. ✅ `GBMSimulator.get_tickers()` public method added (was accessing `_tickers` directly)
6. ✅ `DEFAULT_CORR` / `CROSS_GROUP_CORR` naming confusion removed
7. ✅ Massive test mock targets fixed (`source._client = MagicMock()` added)

### Remaining issues

**Module-level router + factory function (Low severity)**

`stream.py:16` creates a module-level `router` object, then `create_stream_router()` registers a route on it via closure. Calling `create_stream_router` twice would register the `/prices` route twice on the same router instance. In production this never happens; in tests it is a footgun. The router should be created inside `create_stream_router`, not at module level.

**`PriceCache.version` not under lock (Low severity, CPython-safe)**

```python
@property
def version(self) -> int:
    return self._version  # no lock
```

All other `PriceCache` reads acquire `self._lock`. On CPython the GIL makes this safe, but it is inconsistent and would become a race on no-GIL Python 3.13t+. Low risk given the project scope; worth noting for a course codebase.

**`SimulatorDataSource.add_ticker` skips normalization (Low severity)**

```python
async def add_ticker(self, ticker: str) -> None:
    if self._sim:
        self._sim.add_ticker(ticker)  # no .upper().strip()
```

`MassiveDataSource.add_ticker` does normalize. The inconsistency will not cause issues if the API routes always pass uppercase symbols, but it should be documented or enforced.

**`_run_loop` swallows all exceptions (Informational)**

```python
except Exception:
    logger.exception("Simulator step failed")
```

This is intentional for resilience. A persistent GBM failure would produce log spam but not crash the server. Worth noting that in practice, GBM over a float dict cannot fail — the except block is unreachable under normal conditions.

---

## 5. Test Quality

The 73 tests are well-structured. Notable strengths:

- `test_simulator.py` covers edge cases: empty step, negative correlation, Cholesky rebuild, price rounding.
- `test_cache.py` verifies direction logic, version counter, rounding, and all CRUD paths.
- `test_factory.py` covers the whitespace/empty key edge cases the design doc calls out.
- `test_massive.py` uses `_make_snapshot` helper to construct realistic mock responses.

Gaps:

- **SSE streaming (31% coverage).** No tests exercise `_generate_events`. An `httpx.AsyncClient` with `app` as the ASGI transport could test the generator. At minimum, a unit test that drives the generator directly with a mock cache would validate the version-check logic and disconnect detection.
- **No concurrent write test for `PriceCache`.** Lock correctness is assumed from inspection; a `concurrent.futures.ThreadPoolExecutor` test would verify it empirically.
- **GBM correlation is not statistically tested.** Unlike the design doc's `test_tickers_are_correlated_at_rho_squared`, there is no test that verifies the Cholesky decomposition produces the expected pairwise correlation. A 50,000-sample statistical test would be valuable.

---

## 6. Verdict

The market data backend is well-built. The core components — GBM simulator, price cache, abstract interface, factory, and SSE endpoint — are correct and follow good practices. The prior review identified real issues and they were all resolved.

**Must address before the next component:**
- Implement `GET /api/prices/{ticker}/history` — the main chart has no data source without it.

**Should address:**
- Apply ticker normalization consistently in `SimulatorDataSource.add_ticker`.
- Fix the module-level router instance in `stream.py`.

**Nice to have:**
- Add at least one SSE integration test (even unit-level, driving the generator directly).
- Add the `PriceCache.version` property under the lock for consistency.
- Add a statistical correlation test to the simulator suite.

The architecture integrates cleanly with the rest of the application. The `add_ticker` / `remove_ticker` interface is straightforward to call from watchlist and trade routes. The PriceCache consumption API (`get()`, `get_price()`, `get_all()`) is minimal and sensible for portfolio valuation and trade execution.
