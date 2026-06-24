#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

WITH_DB_VOLUME="false"

if [ "${1:-}" = "--with-db-volume" ]; then
  WITH_DB_VOLUME="true"
fi

echo "=== Cleaning local development environment ==="

if [ "$WITH_DB_VOLUME" = "true" ]; then
  echo "WARNING: this will remove Docker containers AND the database volume."
  read -r -p "Are you sure? Type 'yes' to continue: " CONFIRM

  if [ "$CONFIRM" = "yes" ]; then
    docker compose down -v --remove-orphans
    echo "Docker containers, network and database volume removed."
  else
    echo "Skipped Docker volume removal."
  fi
else
  docker compose down --remove-orphans || true
  echo "Docker containers/network removed. Database volume preserved."
fi

echo "Removing Python virtual environment and caches..."

rm -rf .venv
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo ""
echo "Clean completed."
echo ""
echo "To rebuild the environment:"
echo "  ./scripts/setup_environment.sh"
echo "  ./scripts/db_rebuild_populate_validate.sh"
echo ""
echo "To also delete the database volume, run:"
echo "  ./scripts/clean_environment.sh --with-db-volume"
