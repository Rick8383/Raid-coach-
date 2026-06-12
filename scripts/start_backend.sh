#!/usr/bin/env bash
# Démarre l'API FastAPI en local (SQLite par défaut, data/raid_coach.db).
set -euo pipefail
cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -r requirements.txt
fi

echo "API : http://localhost:8000 — docs : http://localhost:8000/docs"
exec ./.venv/bin/python -m uvicorn api.main:app --reload --host 0.0.0.0 --port "${PORT:-8000}"
