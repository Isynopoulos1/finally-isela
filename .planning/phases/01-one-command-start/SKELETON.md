# Walking Skeleton — FinAlly

**Phase:** 1
**Generated:** 2026-09-20

> **Brownfield skeleton.** The repo already carries a first implementation (commit `d3abe5e`). This
> document does not propose an architecture to build — it **records and pins the architecture that
> already exists** and that Phase 1 proves by running it. Later phases build on these decisions;
> changing one is a cross-phase event, not a local edit.

## Capability Proven End-to-End

A developer runs one command and gets a working FinAlly app on `http://localhost:8000`, backed by a
SQLite database that was created and seeded automatically on first start and that survives stopping
and restarting the container.

This is the whole stack in one path: Docker image → FastAPI process → lazy SQLite init → seed →
HTTP response → static frontend served from the same origin.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Packaging | Single Docker image, single port 8000 | One command for the reader; no compose, no service orchestration in production (PLAN.md §3) |
| Image build | Two stages: `node:24-slim` builds the Next.js static export, `python:3.12-slim` + uv serves it | Keeps Node out of the runtime image. **Verified building cleanly at planning time** — PLAN.md §11 says Node 20, the Dockerfile uses 24; the build succeeds, so the Dockerfile wins (D-08 discretion note) |
| Backend | FastAPI, dependencies managed by `uv` from a committed `uv.lock` | Reproducible, frozen installs (`uv sync --frozen`); no unpinned packages enter the image |
| Frontend delivery | Next.js `output: 'export'`, copied to `backend/static`, mounted at `/` after the API routers | Same origin for `/api/*`, so no CORS anywhere in the project (UI-13) |
| Database | SQLite at `/app/db/finally.db`, lazily created on first `get_connection()` | No migration step, no database server, no manual setup |
| Schema | Raw DDL in `backend/db/schema.py`, `CREATE TABLE IF NOT EXISTS`, **no `user_id` columns**, `users_profile` singleton (`CHECK (id = 1)`), `chat_messages.action_summary` nullable TEXT | `planning/DECISIONS.md` items 6 and 10 are the source of truth, not PLAN.md §7 (**D-01**) |
| Migrations | None. A schema change means destroying the database and letting it re-seed | **D-03**; reset commands are documented in the README |
| Snapshots | `portfolio_snapshots` written at seed time and after each trade only — no background timer | **D-02** / DECISIONS.md item 7; the P&L line moves only when the user trades |
| Persistence | Named Docker volume `finally-data` mounted at `/app/db` | `PROJECT_ROOT` in `connection.py` resolves to `/app` in the container, so the default DB path lands exactly on the mount |
| Configuration | `.env` at the project root, passed with `docker run --env-file`; never copied into the image | `.dockerignore` excludes `.env` and `db/*.db`, so secrets cannot reach a layer (DEP-05) |
| Health | `GET /api/health` → `{"status","market_provider"}`, plus a Dockerfile `HEALTHCHECK` using a stdlib `urllib` probe | `python:3.12-slim` has no curl; stdlib avoids adding a package (**D-08**). Health answers 200 only after the lifespan completes, which is what a readiness probe needs |
| Lifecycle scripts | `scripts/start_mac.sh` / `stop_mac.sh` and PowerShell twins; always build, guard on `.env`, poll health, clean up on failure | **D-04** through **D-07**, mirrored to Windows by **D-10** |
| Naming | image `finally`, container `finally-app`, volume `finally-data`, port `8000` | Shared by the scripts and `docker-compose.yml`; changing one requires changing all |

## Stack Touched in Phase 1

- [x] Project scaffold — two-stage Dockerfile, uv-managed backend, Next.js static export
- [x] Routing — `GET /api/health` plus the static mount at `/`
- [x] Database — a real write (lazy `init_db` + `seed`) and a real read (`/api/portfolio`, `/api/watchlist`)
- [x] UI — the built frontend is served from the same origin; `GET /` returns 200
- [x] Deployment — a documented local full-stack run: `./scripts/start_mac.sh`

## Out of Scope (Deferred to Later Slices)

Explicit, so later phases do not re-litigate Phase 1's minimalism:

- Browser auto-open after start — declined (**D-06**, CONTEXT `<deferred>`)
- A one-command database reset script — the manual commands are documented instead (**D-03**)
- Container-based E2E via `docker-compose.test.yml` — DECISIONS.md item 9; E2E runs locally against uvicorn
- Non-root container user — accepted risk at ASVS L1, recorded as threat `T-01-03` for a later hardening pass
- Authentication and `user_id` columns — out of scope for v1 (REQUIREMENTS.md "Out of Scope"); EXT-03
- Price history endpoint — deferred as EXT-01; sparklines accumulate from SSE since page load
- Cloud deployment / Terraform — EXT-02, stretch goal

## Known Verification Limit

**DEP-04 (Windows scripts) is unverified.** No PowerShell interpreter and no Windows host is available
on the development machine, so `start_windows.ps1` and `stop_windows.ps1` are verified by reading plus
mechanical source assertions only (**D-10**). Every other Phase 1 requirement is proven by a real run.

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering the decisions above:

- **Phase 2** — ten tickers tick live in the dark terminal UI, via the SSE stream and the simulator
- **Phase 3** — the user curates the watchlist and drills into one ticker on the main chart
- **Phase 4** — the user trades the simulated $10,000 and the portfolio responds everywhere
- **Phase 5** — the AI assistant analyzes the portfolio and executes trades and watchlist changes
- **Phase 6** — the full demo journey is proven green in the shipped container
