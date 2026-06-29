#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d --remove-orphans
docker compose ps

echo ""
echo "pgAdmin connection:"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Maintenance database: ibd_postgres"
echo "  Username: ibd_postgres"
echo "  Password: ibd_secretpassword"
