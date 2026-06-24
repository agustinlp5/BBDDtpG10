#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Starting PostgreSQL container ==="
docker compose up -d
docker compose ps

echo ""
echo "PostgreSQL is running."
echo ""
echo "pgAdmin connection:"
echo "  Name: IBD PostgreSQL"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Maintenance database: ibd_postgres"
echo "  Username: ibd_postgres"
echo "  Password: ibd_secretpassword"
