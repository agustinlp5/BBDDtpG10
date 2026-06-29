#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PAGER=cat
export COMPOSE_INTERACTIVE_NO_CLI=1

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="ibd_postgres"
DB_USER="ibd_postgres"
DB_PASSWORD="ibd_secretpassword"

GENERATE_SQL="true"
VALIDATE_ONLY="false"

for arg in "$@"; do
  case "$arg" in
    --no-generate)
      GENERATE_SQL="false"
      ;;
    --validate-only)
      VALIDATE_ONLY="true"
      GENERATE_SQL="false"
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage:"
      echo "  ./scripts/db_rebuild_populate_validate.sh"
      echo "  ./scripts/db_rebuild_populate_validate.sh --no-generate"
      echo "  ./scripts/db_rebuild_populate_validate.sh --validate-only"
      exit 1
      ;;
  esac
done

echo "=== Checking required commands ==="

for cmd in docker psql; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: '$cmd' is not installed or not available in PATH."
    exit 1
  fi
done

echo "=== Starting PostgreSQL ==="
docker compose up -d --remove-orphans

echo "=== Waiting for PostgreSQL to accept connections ==="

until PGPASSWORD="$DB_PASSWORD" psql -X \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -c "SELECT 1;" >/dev/null 2>&1; do
  sleep 1
done

if [ "$VALIDATE_ONLY" = "false" ]; then
  if [ "$GENERATE_SQL" = "true" ]; then
    echo "=== Generating population SQL ==="
    if [ -x ".venv/bin/python" ]; then
      .venv/bin/python scripts/generar_poblado.py --config config/poblado_config.json
    else
      python3 scripts/generar_poblado.py --config config/poblado_config.json
    fi
  else
    echo "=== Skipping SQL generation ==="
  fi

  echo "=== Recreating schema ==="

  PGPASSWORD="$DB_PASSWORD" psql -X \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    -f "sql/01_creacion_de_tablas.sql"

  echo "=== Loading generated data ==="

  PGPASSWORD="$DB_PASSWORD" psql -X \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    -f "sql/02_populado_datos.sql"
else
  echo "=== Validate-only mode: skipping schema recreation and data load ==="
fi

echo "=== Running validations ==="

PGPASSWORD="$DB_PASSWORD" psql -X \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -f "sql/03_validaciones_populado.sql"

echo ""
echo "Done."
echo ""
echo "pgAdmin connection:"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Maintenance database: ibd_postgres"
echo "  Username: ibd_postgres"
echo "  Password: ibd_secretpassword"
