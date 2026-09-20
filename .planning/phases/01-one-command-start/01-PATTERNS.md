# Phase 1: One-Command Start - Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 8 modified (+ 1 conditional), 0 new
**Analogs found:** 8 / 8 (all brownfield; each file is its own base, cross-platform pairs are each other's analog)

All paths below were verified git-tracked (`git ls-files`). No gitignored mirrors are referenced. `.env` exists on disk but is gitignored and secret; only `.env.example` is cited.

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `scripts/start_mac.sh` | script (container lifecycle) | request-response (docker CLI + HTTP health poll) | itself (current version); `scripts/start_windows.ps1` as behavioral twin | exact |
| `scripts/start_windows.ps1` | script (container lifecycle) | request-response | `scripts/start_mac.sh` (mirror), itself for PS idioms | exact |
| `scripts/stop_mac.sh` | script | request-response | `scripts/stop_windows.ps1` (twin) | exact |
| `scripts/stop_windows.ps1` | script | request-response | `scripts/stop_mac.sh` (twin) | exact |
| `Dockerfile` | config (image build) | batch | itself; add `HEALTHCHECK` before `CMD` | exact |
| `docker-compose.yml` | config | batch | itself; only touch if HEALTHCHECK/names need alignment | exact |
| `README.md` (reset commands + quick start wording) | doc | n/a | itself (`## Stopping` section as insertion model) | exact |
| `.dockerignore` / `.env.example` / `.gitignore` | config | n/a | themselves; expected no change (verify only) | exact |
| `backend/api/health.py`, `backend/main.py`, `backend/db/{connection,schema,seed}.py` | route / service / model | request-response, CRUD | themselves; D-01/D-03 say keep as is, verify only | exact |

Related test analog for verification wiring: `backend/tests/test_api_health.py`, `backend/tests/test_db_seed.py`, `backend/tests/test_db_connection.py` (exist, untouched). E2E analog: `test/scripts/start-app.sh` (local uvicorn, not Docker, per DECISIONS.md #9; leave alone).

## Pattern Assignments

### `scripts/start_mac.sh` (script, request-response)

**Analog:** itself, `/Users/iselaalarcon/Documents/ia-curse/finally/scripts/start_mac.sh`

**Header, constants, root resolution** (lines 1-12) - keep verbatim:
```bash
#!/usr/bin/env bash
# Build (if needed) and run the FinAlly Docker container.
set -euo pipefail

IMAGE_NAME="finally"
CONTAINER_NAME="finally-app"
VOLUME_NAME="finally-data"
PORT=8000

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
```

**`--build` flag parsing** (lines 14-19) - D-04: no longer needed; delete the loop and `BUILD` var (or leave a no-op accept). Update the header comment ("Build (if needed)" becomes "Build and run"):
```bash
BUILD=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    BUILD=true
  fi
done
```

**Idempotence: already running / stale container** (lines 21-29) - keep; this is what makes run-twice safe (D-09). Note ordering: today the "already running" exit happens before build and before the `.env` check. Decide whether the D-05 `.env` check goes before or after this (D-05 says "before building"; putting it first is simplest but would block `start` on an already-running container if `.env` was later removed; either satisfies the decision):
```bash
if [[ "$(docker ps -q -f name="^${CONTAINER_NAME}$")" != "" ]]; then
  echo "FinAlly is already running at http://localhost:${PORT}"
  exit 0
fi

# Remove a stopped container with the same name, if present.
if [[ "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" != "" ]]; then
  docker rm "${CONTAINER_NAME}" >/dev/null
fi
```

**Build gate to change (D-04)** (lines 31-34): drop the condition, always build.
```bash
if [[ "$BUILD" == true ]] || [[ "$(docker images -q "${IMAGE_NAME}")" == "" ]]; then
  echo "Building ${IMAGE_NAME} image..."
  docker build -t "${IMAGE_NAME}" .
fi
```

**`.env` check to change (D-05)** (lines 36-38): currently a warning to stderr; make it a hard exit and move it above the build. Keep the existing message text, which already matches the decision wording:
```bash
if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
  echo "Warning: .env not found at project root. Copy .env.example to .env and set OPENROUTER_API_KEY." >&2
fi
```
Target shape: `echo "Error: .env not found. Copy .env.example to .env and set OPENROUTER_API_KEY." >&2; exit 1` (same `>&2` convention).

**Run + URL** (lines 40-47) - keep the `docker run -d` flags exactly (names/volume/port must match `docker-compose.yml`); insert the health poll (D-06) and failure cleanup (D-07) between `docker run` and the final `echo`:
```bash
docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8000" \
  -v "${VOLUME_NAME}:/app/db" \
  --env-file "${PROJECT_ROOT}/.env" \
  "${IMAGE_NAME}"

echo "FinAlly is running at http://localhost:${PORT}"
```
New pieces (no in-repo analog for the poll; use standard bash, `curl` is available on macOS/Linux hosts): loop N times with `curl -fs "http://localhost:${PORT}/api/health" >/dev/null && break; sleep 1`; on timeout run `docker logs --tail 30 "${CONTAINER_NAME}" >&2`, then `docker rm -f "${CONTAINER_NAME}" >/dev/null`, `exit 1`. Note `set -e` is on: guard the curl in an `if`/`||` so a failed probe does not abort the script.

Error-output convention used in this repo: messages to stderr with `>&2`; quiet docker calls with `>/dev/null`.

---

### `scripts/start_windows.ps1` (script, request-response)

**Analog:** `scripts/start_mac.sh` for behavior (mirror D-04..D-07); itself for PowerShell idioms. Windows file is at `/Users/iselaalarcon/Documents/ia-curse/finally/scripts/start_windows.ps1`.

**Header, params, constants, root** (lines 1-16) - `-Build` switch is the counterpart of `--build`; per D-04 accept and ignore (keep the `param` block so old invocations do not error) or remove:
```powershell
#Requires -Version 5.1
# Build (if needed) and run the FinAlly Docker container.
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$ImageName = "finally"
$ContainerName = "finally-app"
$VolumeName = "finally-data"
$Port = 8000

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot
```

**Idempotence** (lines 18-27) - keep:
```powershell
$running = docker ps -q -f "name=^${ContainerName}$"
if ($running) {
    Write-Host "FinAlly is already running at http://localhost:$Port"
    exit 0
}

$stopped = docker ps -aq -f "name=^${ContainerName}$"
if ($stopped) {
    docker rm $ContainerName | Out-Null
}
```

**Build gate (D-04)** (lines 29-33): remove the `$Build -or -not $imageExists` condition:
```powershell
$imageExists = docker images -q $ImageName
if ($Build -or -not $imageExists) {
    Write-Host "Building $ImageName image..."
    docker build -t $ImageName .
}
```

**`.env` check (D-05)** (lines 35-38): `Write-Warning` becomes an error exit above the build:
```powershell
$envPath = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envPath)) {
    Write-Warning ".env not found at project root. Copy .env.example to .env and set OPENROUTER_API_KEY."
}
```

**Run + URL** (lines 40-47) - keep flags; add health poll (D-06/D-07) after `docker run`:
```powershell
docker run -d `
    --name $ContainerName `
    -p "${Port}:8000" `
    -v "${VolumeName}:/app/db" `
    --env-file $envPath `
    $ImageName

Write-Host "FinAlly is running at http://localhost:$Port"
```
Windows-specific pitfalls for the planner (cannot be run on this Mac, D-10):
- `$ErrorActionPreference = "Stop"` does not stop on native command non-zero exit in PS 5.1; check `$LASTEXITCODE` after `docker build`/`docker run` if a hard failure is wanted.
- Health probe: use `Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$Port/api/health"` inside `try/catch` (PS 5.1 needs `-UseBasicParsing`; non-2xx throws). Do not rely on `curl` (aliased to `Invoke-WebRequest` in 5.1).
- Failure path: `docker logs --tail 30 $ContainerName`, `docker rm -f $ContainerName | Out-Null`, `exit 1`.
- Keep `-f "name=^${ContainerName}$"` quoting exactly as is (works today).
- Keep timeout/interval/log-line counts identical to the mac script so behavior mirrors.

---

### `scripts/stop_mac.sh` (script, request-response)

**Analog:** `scripts/stop_windows.ps1` (twin). Current file, lines 1-15, is already correct for D-07's "so a re-run starts clean" and stops the container while preserving the volume; expected no change beyond confirming behavior:
```bash
#!/usr/bin/env bash
# Stop and remove the FinAlly container. Data volume is preserved.
set -euo pipefail

CONTAINER_NAME="finally-app"

if [[ "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" == "" ]]; then
  echo "FinAlly is not running."
  exit 0
fi

docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "FinAlly stopped."
```

### `scripts/stop_windows.ps1` (script, request-response)

**Analog:** `scripts/stop_mac.sh`. Current (lines 1-16):
```powershell
#Requires -Version 5.1
# Stop and remove the FinAlly container. Data volume is preserved.
$ErrorActionPreference = "Stop"

$ContainerName = "finally-app"

$exists = docker ps -aq -f "name=^${ContainerName}$"
if (-not $exists) {
    Write-Host "FinAlly is not running."
    exit 0
}

docker stop $ContainerName | Out-Null
docker rm $ContainerName | Out-Null

Write-Host "FinAlly stopped."
```
Small existing divergence to note: mac tolerates stop/rm failures (`|| true`, stderr discarded); Windows does not swallow them (with PS 5.1 native failures do not throw anyway, so effectively equivalent). Leave unless the planner wants strict parity.

---

### `Dockerfile` (config, batch)

**Analog:** itself, `/Users/iselaalarcon/Documents/ia-curse/finally/Dockerfile` (26 lines). Add HEALTHCHECK (D-08) between `EXPOSE 8000` (line 24) and `CMD` (line 26). Current tail:
```dockerfile
COPY --from=frontend-build /app/frontend/out ./static

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Target pattern (no curl in `python:3.12-slim`; use stdlib, avoids installing packages and keeps layers cached):
```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
```
Notes: `python` resolves to the system interpreter in the image (uv installs the venv separately), stdlib only so this is fine. `urlopen` raises on non-2xx, so exit code is non-zero on failure. Health values (interval/retries) are Claude's discretion (D-08 and discretion list).

Other observed facts for the planner:
- Stage 1 uses `node:24-slim` (line 4); PLAN.md says Node 20. CONTEXT says verify the build works and leave it if so.
- DB path in container: `backend/db/connection.py` `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent` gives `/app` with backend at `/app/backend`, so DB is `/app/db/finally.db`, matching `-v finally-data:/app/db`. The Dockerfile does not `mkdir /app/db`; `connection.py:30` (`mkdir(parents=True, exist_ok=True)`) creates it, and Docker creates named-volume mount points. No Dockerfile change needed for persistence.
- `.dockerignore` (lines 25-27) excludes `db/*.db`, `db/*.db-journal`, `.env`; `backend/tests` and `test` are excluded too. Nothing to change unless verification shows otherwise.

---

### `docker-compose.yml` (config, batch)

**Analog:** itself (14 lines). Names must stay consistent with the scripts (`image: finally`, `container_name: finally-app`, volume `finally-data`, port `8000:8000`):
```yaml
services:
  app:
    build: .
    image: finally
    container_name: finally-app
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - finally-data:/app/db

volumes:
  finally-data:
```
The Dockerfile HEALTHCHECK is inherited by compose automatically; no edit required. Likely outcome: unchanged.

---

### `README.md` (doc)

**Analog:** itself, `/Users/iselaalarcon/Documents/ia-curse/finally/README.md`. Insertion model is the `## Stopping` section (lines 51-55); add a short `## Resetting data` section after it (D-03). Concise per user's style ("Keep README concise"):
```markdown
## Stopping

```bash
./scripts/stop_mac.sh   # stops container; data volume is preserved
```
```
Proposed reset content (commands are real and consistent with names in the repo):
- Docker: `./scripts/stop_mac.sh && docker volume rm finally-data`
- Local (uvicorn / E2E): `rm db/finally.db`

Stale line to fix in the Quick start (lines 15-16): it says `./scripts/start_mac.sh        # builds image and opens http://localhost:8000`, but D-06 says the browser is NOT opened. Change to "builds image, starts container, prints http://localhost:8000". Also line 19 (Windows) is fine as is.

---

### Verify-only files (no expected edits; D-01, D-02, D-03)

**`backend/api/health.py`** (lines 1-10), the target of the HEALTHCHECK and the script poll. Note it reads `request.app.state.provider`, which is only set in the lifespan; health returns 200 only after startup completes, which is what a readiness poll wants:
```python
@router.get("/health")
async def get_health(request: Request):
    return {"status": "ok", "market_provider": request.app.state.provider.name}
```
Mounted at `/api` prefix in `backend/main.py:28`; the static mount at `/` (main.py:34-36) is registered after the routers so `/api/*` wins.

**`backend/db/connection.py`** (lines 14-37): lazy open + `init_db` + `seed` on first `get_connection()`; called from `main.py` lifespan line 19.

**`backend/db/seed.py`** (lines 11-29): guard `if conn.execute("SELECT 1 FROM users_profile").fetchone() is not None: return` makes seeding idempotent across restarts; seeds cash 10000.0, ten tickers (`AAPL GOOGL MSFT AMZN TSLA NVDA META JPM V NFLX`), one starting snapshot (matches D-02).

**`backend/db/schema.py`** (lines 1-50): `CREATE TABLE IF NOT EXISTS` for `users_profile` (id INTEGER, `CHECK (id = 1)`), `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `chat_messages` (with `action_summary TEXT`). Matches D-01/D-03. No `user_id` anywhere.

Existing tests that already cover this behavior (run with backend pytest to support D-09 evidence, not a substitute for the Docker run): `backend/tests/test_api_health.py`, `test_db_seed.py`, `test_db_connection.py`, `test_db_schema.py`.

## Shared Patterns

### Names and ports must match across files
**Sources:** `scripts/start_mac.sh:5-8`, `scripts/start_windows.ps1:9-12`, `docker-compose.yml`
**Apply to:** every Docker-touching file
`finally` (image), `finally-app` (container), `finally-data` (volume, mounted at `/app/db`), port `8000`. Any change to one requires changing all.

### Idempotent lifecycle (already-running exit, stale-container removal)
**Source:** `scripts/start_mac.sh:21-29` and `scripts/start_windows.ps1:18-27`
**Apply to:** both start scripts; keep the check ordering so run-twice is safe (D-09).

### Container-name matching
**Source:** `docker ps -q -f name="^${CONTAINER_NAME}$"` (mac) / `docker ps -q -f "name=^${ContainerName}$"` (Windows)
**Apply to:** start and stop scripts, and any new `docker` commands. The anchored regex avoids matching similarly named containers.

### Error output convention
**Source:** `scripts/start_mac.sh:37` (`>&2`), `scripts/start_windows.ps1:37` (`Write-Warning`)
**Apply to:** new failure messages. mac: `echo ... >&2` then `exit 1`. Windows: `Write-Error`/`Write-Host` then `exit 1`. Keep user-facing message text identical across the two platforms (D-10 "mirror").

### Mirror rule for the four scripts
Every behavior change in `start_mac.sh` needs the same change in `start_windows.ps1` (D-10). Suggested single set of constants to reuse in both: health URL `http://localhost:8000/api/health`, poll interval and timeout chosen once (discretion), log tail size chosen once.

## No Analog Found

| File / Piece | Role | Data Flow | Reason |
|--------------|------|-----------|--------|
| Health-poll loop in `start_mac.sh` / `start_windows.ps1` | script logic | request-response | No polling or curl usage exists in any repo script; use standard bash loop / `Invoke-WebRequest` try/catch as sketched above |
| `HEALTHCHECK` instruction in `Dockerfile` | config | request-response | None exists in the repo; use the stdlib Python one-liner sketched above |
| Failure cleanup (`docker logs --tail`, `docker rm -f`, non-zero exit) | script logic | request-response | `stop_mac.sh` has the rm pattern, but no log-dump-on-failure precedent exists |

## Metadata

**Analog search scope:** `scripts/`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `README.md`, `backend/api/health.py`, `backend/main.py`, `backend/db/*`, `test/scripts/start-app.sh`, `backend/tests/` (listing only)
**Files scanned:** ~20 (all read directly; `.planning/codebase/*.md` not used; `.env` not read)
**Pattern extraction date:** 2026-09-20
