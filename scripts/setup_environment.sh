#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Setting up minimal Python environment ==="

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo ""
echo "Environment ready."
echo "Activate manually with:"
echo "  source .venv/bin/activate"
