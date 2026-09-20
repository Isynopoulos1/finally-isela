---
last_mapped_commit: 85c7a055767e7430f4fbc22913eacde18041a246
last_mapped_at: 2026-09-20
---
# Technology Stack

**Analysis Date:** 2026-09-20

## Languages

**Primary:**

- TypeScript 5.x - Frontend application (`frontend/`)
- Python 3.12 - Backend server and all server logic (`backend/`)

**Secondary:**

- JavaScript (Vite configuration and tooling)

## Runtime

**Environment:**

- Node.js 24-slim (Docker build stage for frontend)
- Python 3.12-slim (Docker runtime for backend)

**Package Manager:**

- npm (frontend) - lockfile present: `frontend/package-lock.json`
- uv (backend) - modern Python project manager - lockfile present: `backend/uv.lock`

## Frameworks

**Frontend:**

- Next.js 16.3.5 - Full-stack React framework, configured for static export (`output: "export"` in `frontend/next.config.ts`)
- React 19.2.8 - UI library
- TypeScript 5.x - Type safety

**Backend:**

- FastAPI 0.141.1+ - Async web framework for REST API and SSE streaming
- Uvicorn 0.53.0+ - ASGI server running on port 8000
- Pydantic 2.13.5+ - Data validation and settings management

**Testing:**

- Vitest 5.0.1 - Frontend unit/integration tests with jsdom environment
- pytest 8.0+ - Backend unit tests
- pytest-asyncio 0.24+ - Async test support for FastAPI routes
- Playwright 1.63.0 - E2E browser automation tests

**Build/Dev:**

- Next.js build system (Turbopack for dev, static export for prod)
- uv for Python dependency lockfile management
- Ruff 0.6+ - Python linter/formatter

**Styling:**

- Tailwind CSS 4.x - Utility-first CSS framework
- PostCSS 4.x - CSS transformation via `@tailwindcss/postcss` plugin
- Tailwind CSS TypeScript types via `@tailwindcss/postcss`

## Key Dependencies

**Frontend (Critical):**

- `lightweight-charts` 5.2.1 - Canvas-based charting library for real-time price charts and sparklines
- `react-dom` 19.2.8 - React rendering for browser DOM
- `@vitejs/plugin-react` 6.1.1 - Vite + React support for test environment

**Frontend (Testing):**

- `@testing-library/react` 16.3.3 - React component testing utilities
- `@testing-library/jest-dom` 7.0.1 - Jest matchers for DOM assertions
- `@testing-library/user-event` 14.6.7 - User interaction simulation
- `jsdom` 30.1.0 - Simulated DOM for unit tests

**Frontend (Type Safety):**

- `@types/react` 19.x - React type definitions
- `@types/react-dom` 19.x - React DOM type definitions
- `@types/node` 26.x - Node.js type definitions (Next.js requirement)

**Frontend (Dev):**

- `eslint` 9.x - JavaScript/TypeScript linting via flat config
- `eslint-config-next` 16.3.5 - Next.js ESLint rules (core web vitals + TypeScript)

**Backend (Critical):**

- `fastapi` - Async web framework for `/api/*` routes and SSE streaming at `GET /api/stream/prices`
- `httpx` 0.27+ - Async HTTP client for Massive API calls
- `litellm` 1.101.0+ - Unified LLM interface to OpenRouter API
- `openai` 2.54.0+ - OpenAI SDK for structured outputs (used by LiteLLM for Pydantic validation)
- `pydantic` 2.13.5+ - Data validation for request/response schemas and LLM structured output parsing
- `python-dotenv` 1.2.3+ - Load environment variables from `.env` file
- `uvicorn[standard]` 0.53.0+ - ASGI server with full feature set

**Backend (Dev):**

- `pytest` 8.0+ - Test framework
- `pytest-asyncio` 0.24+ - Async test support
- `ruff` 0.6+ - Fast Python linter/formatter
- `httpx2` 2.13.0+ - Testing utilities (likely for mocking HTTP)

## Configuration

**Environment:**

- `.env` file (git-ignored, `.env.example` provided) contains:
  - `OPENROUTER_API_KEY` - Required for LLM chat via OpenRouter
  - `MASSIVE_API_KEY` - Optional for live market data (simulator used by default)
  - `LLM_MOCK` - Optional, set to `"true"` for deterministic mock responses in testing
- `python-dotenv` loads `.env` in backend at `backend/llm/client.py`

**Frontend Build:**

- `frontend/tsconfig.json` - TypeScript configuration with strict mode, path aliases (`@/*` → `./src/*`)
- `frontend/next.config.ts - Static export configuration (`output: "export"`, unoptimized images)
- `frontend/vitest.config.mts` - Vitest configuration: jsdom environment, React plugin, setup file at `vitest.setup.ts`
- `frontend/eslint.config.mjs` - Flat ESLint config: Next.js web vitals + TypeScript, ignores `.next/`, `out/`, `build/`
- `frontend/postcss.config.mjs` - PostCSS configured with Tailwind CSS plugin

**Backend Configuration:**

- `backend/pyproject.toml` - uv project manifest with dependencies, dev tools, test config
  - `pytest.ini_options` set to async mode `"auto"`, test path: `tests/`
  - Ruff: line-length 100, target Python 3.12
- `backend/llm/client.py` - Hardcoded: `MODEL = "openrouter/openai/gpt-oss-120b"`, `EXTRA_BODY = {"provider": {"order": ["cerebras"]}}`

## Platform Requirements

**Development:**

- Node.js 24.x (for frontend `npm install` and `next dev`)
- Python 3.12.x (for backend `uv sync` and test runs)
- SQLite 3 (bundled in Python standard library and via Docker)

**Production:**

- Docker (single container image, multi-stage: Node → Python)
- Docker volume mount at `/app/db` for SQLite persistence
- Port 8000 exposed (FastAPI server)
- Environment variables injected via `--env-file .env` or Docker secrets

## Docker Build

- **Stage 1 (frontend-build):** `node:24-slim` → builds Next.js static export to `frontend/out/`
- **Stage 2 (backend/runtime):** `python:3.12-slim` → installs uv, syncs Python deps, copies frontend static files into `backend/static/`, runs FastAPI on port 8000
- **Multi-stage result:** Single image with Next.js build output and FastAPI server

---

*Stack analysis: 2026-09-20*
