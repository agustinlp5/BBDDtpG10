#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Stopping and removing project containers/network ==="
docker compose down --remove-orphans

echo ""
echo "Docker Compose project is down."
echo "Database volume was preserved."
echo "To start again:"
echo "  ./scripts/db_up.sh"
