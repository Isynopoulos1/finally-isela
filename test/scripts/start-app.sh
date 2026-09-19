#!/usr/bin/env bash
# Builds the frontend, wires it into backend/static, resets the SQLite db to a
# fresh seed, and launches the backend with LLM_MOCK=true. Used as Playwright's
# webServer command (see ../playwright.config.ts) — per planning/DECISIONS.md #9,
# E2E runs locally against uvicorn serving the built static export, not Docker.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="${FINALLY_PORT:-8001}"

cd "$ROOT_DIR/frontend"
npm run build

rm -rf "$ROOT_DIR/backend/static"
cp -r "$ROOT_DIR/frontend/out" "$ROOT_DIR/backend/static"

rm -f "$ROOT_DIR/db/finally.db"

cd "$ROOT_DIR/backend"
export LLM_MOCK=true
exec uv run uvicorn main:app --port "$PORT"
