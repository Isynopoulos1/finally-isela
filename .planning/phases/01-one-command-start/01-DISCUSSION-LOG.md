# Phase 1: One-Command Start - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-20
**Phase:** 1-One-Command Start
**Areas discussed:** Schema source of truth, Start script behavior, Container health & failure, How Phase 1 is verified

---

## Schema source of truth

**Q1 — Which document is the source of truth?**

| Option | Description | Selected |
|--------|-------------|----------|
| DECISIONS.md (Recommended) | Keep code: no user_id, action_summary TEXT, seed snapshot; rewrite DB-03 | ✓ |
| PLAN.md §7 literally | Add user_id everywhere and a JSON actions column | |
| Mixed | Pick per item | |

**User's choice:** DECISIONS.md

**Q2 — Snapshots: trade-only or also 30s background task?**

| Option | Description | Selected |
|--------|-------------|----------|
| Trade-only + seed (Recommended) | Matches code and DECISIONS #7; amend PORT-08 | ✓ |
| Add 30s background task | Follows PLAN.md; Phase 4 code change | |
| Decide in Phase 4 | Leave PORT-08 as written | |

**User's choice:** Trade-only + seed

**Q3 — Schema drift policy for existing db/volume?**

| Option | Description | Selected |
|--------|-------------|----------|
| No migrations (Recommended) | Schema change = delete DB/volume; document reset | ✓ |
| Detect and fail loudly | Startup schema check with a clear message | |
| Add real migrations | Versioned migration logic | |

**User's choice:** No migrations

---

## Start script behavior

**Q1 — Stale image when no --build?**

| Option | Description | Selected |
|--------|-------------|----------|
| Always build (Recommended) | Layer cache makes it fast; never stale | ✓ |
| Keep --build flag | Matches PLAN.md; stale-image risk | |
| Build only if sources changed | Timestamp/hash logic in shell | |

**User's choice:** Always build

**Q2 — Missing .env?**

| Option | Description | Selected |
|--------|-------------|----------|
| Stop with a clear message (Recommended) | Exit before building | ✓ |
| Copy .env.example automatically | Continue with warning | |
| Run without an env file | Skip --env-file | |

**User's choice:** Stop with a clear message

**Q3 — Readiness before printing URL?**

| Option | Description | Selected |
|--------|-------------|----------|
| Wait for /api/health (Recommended) | Poll with timeout, then print URL | ✓ |
| Print URL immediately | As today | |
| Wait, and open the browser | Same wait plus auto-open | |

**User's choice:** Wait for /api/health

---

## Container health & failure

**Q1 — HEALTHCHECK in the Dockerfile?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, in the Dockerfile (Recommended) | Self-describing image; needs curl or a Python one-liner | ✓ |
| No, script polling is enough | Keep Dockerfile as is | |

**User's choice:** Yes, in the Dockerfile

**Q2 — Container never becomes healthy?**

| Option | Description | Selected |
|--------|-------------|----------|
| Show logs, stop container, exit 1 (Recommended) | Clean re-run | ✓ |
| Show logs, leave container running | Allows docker exec inspection | |

**User's choice:** Show logs, stop container, exit 1

---

## How Phase 1 is verified

**Q1 — Verification depth on this Mac?**

| Option | Description | Selected |
|--------|-------------|----------|
| Real Docker run (Recommended) | Start, health, seed via API, stop, restart, persistence, idempotence | ✓ |
| Static review only | Read scripts against requirements | |

**User's choice:** Real Docker run

**Q2 — Windows .ps1 scripts can't be run here (DEP-04)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror the mac script, review by reading (Recommended) | Same behavior; mark unverified on Windows | ✓ |
| Drop Windows scripts | Removes DEP-04 (scope change) | |
| Verify on Windows later | Leave .ps1 as written | |

**User's choice:** Mirror the mac script, review by reading

---

## Claude's Discretion

- Health-wait timeout, poll interval, log line count, HEALTHCHECK parameters.
- Whether docker-compose.yml needs edits; script message wording.

## Deferred Ideas

- Browser auto-open; a one-command DB reset script; container-based E2E (already deferred by DECISIONS.md #9).
