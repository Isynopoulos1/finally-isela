# Phase 1: One-Command Start - Context

**Gathered:** 2026-09-20
**Status:** Ready for planning

<domain>
## Phase Boundary

One command (`scripts/start_mac.sh` or `start_windows.ps1`) builds and runs the single container on port 8000 with a pre-seeded SQLite database that survives stop/start. Covers the Dockerfile, start/stop scripts, `.env` handling, the health endpoint, and database lazy-init/seed/persistence. Existing code is reused and verified against these decisions; nothing here adds new user-facing capabilities.

</domain>

<decisions>
## Implementation Decisions

### Schema and data
- **D-01:** `planning/DECISIONS.md` is the source of truth for the schema, not PLAN.md §7. Keep the existing `backend/db/schema.py` as is: no `user_id` columns, `users_profile` singleton row (`id = 1`), `chat_messages.action_summary` nullable TEXT (not a JSON `actions` column). Requirement DB-03 is rewritten to say this. — **Reversibility:** costly — adding `user_id` later touches every query in `backend/db/repository.py` and every table.
- **D-02:** Portfolio snapshots are recorded at seed time and after each trade only. There is no 30-second background task. Requirement PORT-08 and Phase 4 success criterion 5 are amended to match. The P&L line moves only when the user trades.
- **D-03:** No migrations. `CREATE TABLE IF NOT EXISTS` stays. A schema change in a later phase means deleting `db/finally.db` (local) or the `finally-data` volume (Docker). Document the reset commands in the README.

### Start script behavior
- **D-04:** The start script always runs `docker build` (Docker's layer cache makes an unchanged rebuild near-instant), so it never runs a stale image. The `--build` flag is no longer needed; accepting and ignoring it for compatibility is fine.
- **D-05:** If `.env` is missing, exit before building with a clear message ("Copy .env.example to .env and set OPENROUTER_API_KEY"). No auto-copy, no running without an env file.
- **D-06:** After `docker run -d`, poll `http://localhost:8000/api/health` with a short timeout, then print the URL. Do not open the browser automatically.
- **D-07:** If the container never becomes healthy: print the last container log lines, stop and remove the container, exit non-zero, so a re-run starts clean.
- **D-08:** The Dockerfile gets a `HEALTHCHECK` on `/api/health`, so `docker ps` shows healthy/unhealthy. `python:3.12-slim` has no curl; use a Python one-liner or install curl.

### Verification
- **D-09:** Verify with a real Docker run on this Mac (Docker 29.6 is available): start, `/api/health`, seeded cash and ten tickers via the API, stop, start again, confirm the data persisted on the `finally-data` volume, then run start twice to confirm idempotence. Evidence from the run, not code reading.
- **D-10:** `scripts/start_windows.ps1` and `stop_windows.ps1` mirror the updated mac behavior (D-04 to D-07). They cannot be run on this Mac: verify by careful reading and record DEP-04 as "unverified on Windows" in the phase verification notes.

### Claude's Discretion
- Health-wait timeout, poll interval, number of log lines printed, and HEALTHCHECK interval/retries values.
- Whether `docker-compose.yml` needs edits to stay consistent with the Dockerfile (it is an optional convenience per PLAN.md §4).
- Exact wording of script messages.
- Observation for the planner, not decided: PLAN.md §11 says Node 20 slim, the Dockerfile uses `node:24-slim`. Check that the frontend builds cleanly, and leave it if so.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Specification and decisions
- `planning/PLAN.md` §5 (environment variables), §7 (database), §11 (Docker and deployment) — original spec; where it conflicts with DECISIONS.md, DECISIONS.md wins for the schema (D-01) and snapshots (D-02)
- `planning/DECISIONS.md` — resolved build decisions (#6 no `user_id`, #7 snapshot-on-trade, #9 E2E runs locally not in Docker, #10 `action_summary`)
- `.planning/REQUIREMENTS.md` — DEP-01..05, DB-01..04, SYS-01 (DB-03 and PORT-08 amended by this discussion)
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria

### Files this phase touches
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `.gitignore`
- `scripts/start_mac.sh`, `scripts/stop_mac.sh`, `scripts/start_windows.ps1`, `scripts/stop_windows.ps1`
- `backend/db/connection.py`, `backend/db/schema.py`, `backend/db/seed.py`, `backend/api/health.py`, `backend/main.py`

</canonical_refs>

<code_context>
## Existing Code Insights

Checked against the real files in this session; `.planning/codebase/` was not relied on.

### Reusable Assets
- `Dockerfile`: two-stage build already exists (`node:24-slim` builds `frontend/out`, `python:3.12-slim` with uv serves it from `backend/static`, port 8000). No HEALTHCHECK yet.
- `scripts/start_mac.sh`: already idempotent (exits if running, removes a stopped container). Builds only when no `finally` image exists. Warns on missing `.env` then fails at `docker run`. Prints the URL immediately.
- `scripts/stop_mac.sh`: stops and removes the container, keeps the volume.
- `backend/db/connection.py`: lazy-opens `db/finally.db`, runs `init_db` and `seed` on first use.
- `backend/db/seed.py`: seeds only when `users_profile` is empty: $10,000, ten default tickers, one starting snapshot.
- `backend/api/health.py`: `GET /api/health` returns `{"status": "ok", "market_provider": <name>}`.

### Established Patterns
- DB path is `PROJECT_ROOT / "db" / "finally.db"` where `PROJECT_ROOT` is three parents up from `connection.py`. In the container (`/app/backend/db/connection.py`) that resolves to `/app/db/finally.db`, which matches the `-v finally-data:/app/db` mount.
- `.dockerignore` excludes `.env` and `db/*.db`, so secrets and local data never enter the image. Env vars arrive through `--env-file` at run time.
- E2E tests use `test/scripts/start-app.sh` (local uvicorn on port 8001), not Docker.

### Integration Points
- `docker-compose.yml` builds image `finally`, container `finally-app`, volume `finally-data`. The scripts use the same names; keep them consistent.
- A `finally:latest` image and a local `db/finally.db` already exist on this machine.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Auto-opening the browser after start — PLAN.md calls it optional; declined for now (D-06).
- A one-command database reset script — for now, document the manual reset commands (D-03).
- Container-based E2E (`docker-compose.test.yml`) — already deferred by DECISIONS.md #9.

</deferred>

---

*Phase: 1-One-Command Start*
*Context gathered: 2026-09-20*
