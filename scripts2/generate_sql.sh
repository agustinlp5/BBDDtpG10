#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CONFIG_PATH="${1:-config/poblado_config.json}"

echo "=== Generating SQL files only ==="
echo "Config: $CONFIG_PATH"

if [ -x ".venv/bin/python" ]; then
  .venv/bin/python scripts/generar_poblado.py --config "$CONFIG_PATH"
else
  python3 scripts/generar_poblado.py --config "$CONFIG_PATH"
fi

echo ""
echo "Generated:"
echo "  sql/02_populado_datos.sql"
echo "  sql/03_validaciones_populado.sql"
