#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT}/.devcontainer/docker-compose.ha-mounted.yml"
HA_URL="http://127.0.0.1:8123"
WAIT_SECONDS=180

cd "${ROOT}/.devcontainer"

docker compose -f docker-compose.ha-mounted.yml up -d

deadline=$((SECONDS + WAIT_SECONDS))
echo "Waiting for Home Assistant at ${HA_URL} (up to ${WAIT_SECONDS}s)..."
while (( SECONDS < deadline )); do
  if curl -fsS "${HA_URL}/" >/dev/null 2>&1; then
    echo "Home Assistant is responding."
    echo "Open ${HA_URL} and add the USCCB Daily Readings integration."
    exit 0
  fi
  sleep 3
done

echo "Timed out waiting for Home Assistant." >&2
docker compose -f docker-compose.ha-mounted.yml logs --tail 50
exit 1
