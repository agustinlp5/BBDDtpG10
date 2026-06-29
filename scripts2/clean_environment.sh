#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

WITH_DB_VOLUME="false"

for arg in "$@"; do
  case "$arg" in
    --with-db-volume)
      WITH_DB_VOLUME="true"
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage:"
      echo "  ./scripts/clean_environment.sh"
      echo "  ./scripts/clean_environment.sh --with-db-volume"
      exit 1
      ;;
  esac
done

echo "=== Cleaning environment ==="

if [ "$WITH_DB_VOLUME" = "true" ]; then
  echo "Removing Docker containers, network and database volume..."
  docker compose down -v --remove-orphans || true
else
  echo "Removing Docker containers and network. Database volume is preserved..."
  docker compose down --remove-orphans || true
fi

echo "Removing Python virtual environment..."
rm -rf .venv

echo "Removing Python/Jupyter caches..."
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

echo ""
echo "Clean completed."
echo ""
echo "To rebuild:"
echo "  ./scripts/setup_environment.sh"
echo "  ./scripts/db_rebuild_populate_validate.sh"
