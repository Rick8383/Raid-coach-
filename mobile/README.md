# RAID Coach — App iOS (Phase 4, v1 beta)

React Native (Expo) · iPhone first, Android-ready.

## Démarrer
1. Backend : `uvicorn api.main:app` (repo backend)
2. App : `npm install && npm run ios`
3. Configurer l'URL API : variable `EXPO_PUBLIC_API_URL` (par défaut localhost:8000)

## Écrans v1
- **Check-in** (porte d'entrée quotidienne) : forme, fatigue, sommeil, sciatique → 30 s
- **Aujourd'hui** : compte à rebours sélection + Best Action Today (décision du moteur B10/B14)
- **Objectifs** : readiness élite + progression vers chaque cible sélection

## Architecture
- `src/api/client.ts` — client FastAPI offline-first (cache lecture + file de sync écriture)
- `src/theme/tokens.ts` — design system "tableau de bord opérationnel nocturne"
- Signature visuelle : liseré readiness (vert/jaune/orange/rouge) sur chaque carte

## Publication iPhone
- Beta personnelle : Expo Go (immédiat) ou TestFlight via `eas build --platform ios`
- Compte Apple Developer requis pour TestFlight (99 $/an)
