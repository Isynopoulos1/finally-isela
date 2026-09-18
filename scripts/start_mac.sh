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

BUILD=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    BUILD=true
  fi
done

if [[ "$(docker ps -q -f name="^${CONTAINER_NAME}$")" != "" ]]; then
  echo "FinAlly is already running at http://localhost:${PORT}"
  exit 0
fi

# Remove a stopped container with the same name, if present.
if [[ "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" != "" ]]; then
  docker rm "${CONTAINER_NAME}" >/dev/null
fi

if [[ "$BUILD" == true ]] || [[ "$(docker images -q "${IMAGE_NAME}")" == "" ]]; then
  echo "Building ${IMAGE_NAME} image..."
  docker build -t "${IMAGE_NAME}" .
fi

if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
  echo "Warning: .env not found at project root. Copy .env.example to .env and set OPENROUTER_API_KEY." >&2
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8000" \
  -v "${VOLUME_NAME}:/app/db" \
  --env-file "${PROJECT_ROOT}/.env" \
  "${IMAGE_NAME}"

echo "FinAlly is running at http://localhost:${PORT}"
