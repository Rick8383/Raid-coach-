#!/usr/bin/env bash
# Valide l'ensemble du projet : tests backend (pytest + 4 audits) puis TypeScript mobile.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Backend : pytest (26 tests, inclut les 4 audits 100 samples) ==="
cd "$ROOT/backend"
python3 -m pytest tests/ -q

echo
echo "=== Mobile : TypeScript ==="
cd "$ROOT/mobile"
[ -d node_modules ] || npm install
npm run typecheck
echo "TypeScript : OK"
