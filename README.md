# RAID Coach Elite+

Plateforme de coaching adaptatif pour la préparation à la **sélection RAID** (Police nationale) : 13 moteurs d'entraînement Python (Run, CrossFit, Hyrox, Strength, Nutrition, Coach Brain, RCOS…), une API FastAPI et une app iPhone (React Native / Expo).

> Source de vérité du projet : [`PROJECT_MASTER.md`](PROJECT_MASTER.md)

## Architecture

```
┌─────────────────────────────────┐
│   mobile/ — App iOS (Expo)      │  Check-in 30s · Best Action Today · Objectifs élite
│   offline-first (cache + queue) │
└────────────────┬────────────────┘
                 ▼  HTTP (18 endpoints)
┌─────────────────────────────────┐
│   backend/api — FastAPI         │  Validation Pydantic · façade CoachAPI
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│   backend/engines — Moteurs     │  B1→B14 : core, run, strength, coach_brain,
│   (Python pur, dataclasses)     │  nutrition, rcos, selection_wods, legacy B3-B7
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│   backend/db — Persistance      │  SQLite local (défaut) · PostgreSQL + Redis (prod)
└─────────────────────────────────┘
```

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `backend/engines/` | Moteurs métier B1→B14 (validés par audits 100 samples) |
| `backend/api/` | FastAPI : 13 endpoints moteurs + 5 endpoints persistance |
| `backend/db/` | Schéma 10 tables, 7 repositories, cache compatible Redis |
| `backend/tests/` | 36 tests pytest (API, persistance, régressions, 4 audits) |
| `mobile/` | App Expo/React Native (TypeScript strict) |
| `scripts/` | Scripts de démarrage et de validation |
| `.github/workflows/` | CI : pytest + audits, PostgreSQL/Redis, Docker, TypeScript |

## Prérequis

- **Backend** : Python 3.11+ (3.12 recommandé)
- **Mobile** : Node 18+, l'app **Expo Go** sur iPhone (ou Xcode pour le simulateur)
- **Optionnel** : Docker (stack complète PostgreSQL + Redis)

## Démarrage local

### 1. Backend (SQLite, aucun service externe requis)

```bash
./scripts/start_backend.sh
# API : http://localhost:8000 — documentation interactive : http://localhost:8000/docs
```

Ou manuellement :

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

La base SQLite est créée automatiquement dans `backend/data/raid_coach.db`
(chemin modifiable via la variable d'environnement `RAID_COACH_DB`).

### 2. App mobile

```bash
./scripts/start_mobile.sh
# Scanner le QR code avec Expo Go (iPhone) — l'app pointe sur http://localhost:8000
```

Pour tester sur un iPhone réel avec le backend sur ton Mac, mets l'IP locale du Mac
dans `mobile/.env` : `EXPO_PUBLIC_API_URL=http://192.168.x.x:8000`.

### 3. Stack Docker complète (optionnel)

```bash
docker compose up --build
```

## Tests et validation

```bash
./scripts/run_tests.sh        # tout : pytest backend + TypeScript mobile
```

Ou séparément :

```bash
cd backend && python -m pytest tests/ -v    # 36 tests (inclut les 4 audits 100 samples)
cd mobile && npm run typecheck               # TypeScript strict
```

Les audits historiques restent exécutables individuellement :
`python build1_2_audit.py`, `build12_audit.py`, `build13_audit.py`, `build14_audit.py`.

## Endpoints API (27)

**Moteurs** : `/health` · `/coach/daily-decision` · `/coach/weekly-budget` ·
`/coach/arbitrate-goals` · `/run/hr-profile` · `/run/predictions` · `/run/pace-table` ·
`/strength/generate` · `/strength/pr-estimate` · `/raid/strength-report` ·
`/plans/auto-generate` · `/nutrition/daily-macros` · `/nutrition/selection-day`

**Séance & planning** : `POST /coach/session` (décision + séance détaillée prête à
exécuter, calée sur le planning 3/2/2/3) · `POST /schedule/day` · `POST /schedule/week` ·
`POST /agenda/week` (semaine + intention par jour + séances réalisées) ·
`POST /roadmap` (plan annuel rétro-planifié Base/Build/Peak/Taper jusqu'à 2029 + jalons)

**Profil & analytics** : `GET /profile` · `PATCH /profile` (poids, FC, objectif…) ·
`GET /analytics/snapshot` (forme / fatigue / ACWR / risque, dérivés des données) ·
`GET /sessions/recent`

**Persistance** : `POST /metrics/record` · `POST /sessions/complete` ·
`POST /benchmarks/record` · `GET /metrics/latest` · `GET /benchmarks/{id}/progression`

## Planning police 3/2/2/3

Le calendrier de service est la source de vérité du rythme d'entraînement
(`backend/engines/schedule/`, miroir offline dans `mobile/src/schedule.ts`) :

- **Grande semaine** : service lun/mar/ven/sam/dim → OFF mer/jeu (double séance les jours OFF)
- **Petite semaine** : service mer/jeu → OFF le reste
- **Ancre** : la semaine du lundi **15/06/2026** est une grande semaine ; les semaines alternent ensuite.

L'app affiche la semaine en cours (bande de jours service/OFF) et adapte
automatiquement la décision du coach selon que le jour est travaillé ou non.

## App mobile — écrans

1. **Check-in** (30 s) : pré-rempli depuis le **wearable** (HRV, FC de repos, sommeil),
   complété par les ressentis (forme, fatigue) et l'interrupteur sciatique.
2. **Jour** : compte à rebours sélection, planning 3/2/2/3 du jour, et la meilleure
   action — qui ouvre la **séance détaillée**.
3. **Séance détaillée** : phases (échauffement / corps / retour au calme / 2e séance),
   prescription par bloc, bandeau sécurité sciatique, bouton « Terminer » (offline-first).
4. **Agenda** : navigation semaine par semaine, intention par jour (service / OFF /
   double), séances réalisées cochées, encart « état de forme » (analytics).
5. **Course** : zones de fréquence cardiaque (Z1→Z5) + table d'allures alignées par
   zone, avec sélecteur terrain (route/trail/vallonné/montagne) et gilet lesté.
5. **Nutrition** : macros du jour adaptées au profil et au cyclage glucidique
   (haut les jours OFF, modéré en service).
6. **Objectifs** : readiness élite et progression vers les cibles sélection.
7. **Profil** : données réelles (poids ajustable, FC, VMA, contrainte sciatique, maxes),
   chargées depuis l'API avec cache offline, + **feuille de route → 2029** (frise des
   blocs Base/Build/Peak/Taper et jalons benchmarks, plan annuel RCOS).

Le profil athlète réel (mensurations + maxes) est seedé en base au premier démarrage
et alimente tous les écrans — plus aucune valeur en dur dans l'app.

### Wearable (HRV / sommeil / FC repos)

La couche `mobile/src/wearable/` lit les métriques de santé via une interface
provider : **Apple Santé (HealthKit)** quand l'app tourne dans un build natif
(dev client / EAS, module `react-native-health` chargé dynamiquement), sinon une
**simulation** pour Expo Go / démo. Le check-in pré-remplit le sommeil et envoie
HRV / FC de repos / heures de sommeil au backend (`/metrics/record`, colonnes
`hrv`, `resting_hr`, `sleep_hours` déjà prévues en base).

## Déploiement

L'image Docker du backend est autonome (SQLite embarqué) :

```bash
docker build -t raid-coach-api backend/
docker run -p 8000:8000 -v raid-data:/app/data raid-coach-api
```

Compatible Railway / Render tel quel (la CI vérifie le build + smoke test à chaque push).
Pour PostgreSQL/Redis en production : voir `docker-compose.yml` et le workflow
`backend-validation.yml` (le schéma est validé contre PostgreSQL 16 à chaque push).

L'app iOS se distribue via **EAS / TestFlight** (compte Apple Developer requis) :

```bash
cd mobile && npx eas build --platform ios
```

## Garde-fous métier

- Le coach ne génère **jamais** de séance dangereuse : crise sciatique L5-S1 → intensité plafonnée, alternatives sans charge axiale.
- Readiness RED → récupération uniquement.
- Budget fatigue hebdomadaire (rythme police 3/2/2/3) : 420 SU grande semaine / 620 SU petite semaine, ACWR surveillé.
