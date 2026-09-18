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
