#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose down --remove-orphans

echo ""
echo "Database container stopped."
echo "Database volume was preserved."
