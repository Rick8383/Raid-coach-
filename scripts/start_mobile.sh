#!/usr/bin/env bash
# Démarre l'app Expo (iOS). Prérequis : Node 18+, Xcode ou l'app Expo Go sur iPhone.
set -euo pipefail
cd "$(dirname "$0")/../mobile"

[ -d node_modules ] || npm install

# Pointe l'app vers le backend local par défaut (modifiable dans .env)
[ -f .env ] || cp .env.example .env

exec npx expo start
