#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="ibd_postgres"
DB_USER="ibd_postgres"
DB_PASSWORD="ibd_secretpassword"

echo "=== Checking required commands ==="

for cmd in docker psql; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: '$cmd' is not installed or not available in PATH."
    exit 1
  fi
done

echo "=== Starting PostgreSQL ==="
docker compose up -d

echo "=== Waiting for PostgreSQL to accept connections ==="

until PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -c "SELECT 1;" >/dev/null 2>&1; do
  sleep 1
done

echo "=== Generating population SQL ==="

if [ -x ".venv/bin/python" ]; then
  .venv/bin/python scripts/generar_poblado.py --config config/poblado_config.json
else
  echo "WARNING: .venv not found. Using system python3."
  python3 scripts/generar_poblado.py --config config/poblado_config.json
fi

echo "=== Recreating schema ==="

PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -f "sql/01_creacion_de_tablas.sql"

echo "=== Loading generated data ==="

PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -f "sql/02_populado_datos.sql"

echo "=== Running validations ==="

PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -f "sql/03_validaciones_populado.sql"

echo ""
echo "Database rebuilt, populated and validated successfully."
echo ""
echo "pgAdmin connection:"
echo "  Name: IBD PostgreSQL"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Maintenance database: ibd_postgres"
echo "  Username: ibd_postgres"
echo "  Password: ibd_secretpassword"
