# RAID Coach Elite+ — Backend complet (B1 → B14)

Backend de coaching adaptatif pour préparation à la sélection RAID (Police Nationale).
Tous les moteurs métier + API FastAPI + persistance PostgreSQL/Redis + WODs sélection officiels.

## Structure
```
engines/
├── core/            B1  — Domaine (Athlete, Goal, Session, Metrics, RaidProfile, Memory)
├── run_engine/      B2  — Run Engine Runtime (110 familles, 660 templates, pipeline 8 moteurs)
├── legacy/          B3-B7 — CrossFit, Hyrox, Adaptive, Road To RAID, Analytics, Auto Plan
├── strength/        B8  — Strength Engine (60 familles, 360 templates, e1RM, RAID targets)
├── run_elite/       B9  — HR Zones, Predictions (Riegel), Pace Calculator, 110 familles run
├── coach_brain/     B10 — Fatigue Budget (3/2/2/3), ACWR, Goal Arbitration, Daily Decision
├── nutrition/       B11 — BMR/TDEE, cyclage glucidique, plan jour-J, suppléments
├── rcos/            B14 — Athlete Memory, Digital Twin (Banister), Life Engine, Annual Planner
└── selection_wods.py    — 2 WODs sélection officiels + générateur de variantes
api/
├── main.py          B12 — FastAPI, 13 endpoints
└── services/        B12 — CoachAPI : façade unique sur tous les moteurs
db/                  B13 — Schéma 10 tables, 7 repositories, cache Redis-compatible
```

## Démarrer en local
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
# Docs interactives : http://localhost:8000/docs
```

## Docker
```bash
docker build -t raid-coach-api .
docker run -p 8000:8000 raid-coach-api
```

## Validation
```bash
python -m pytest tests/ -v   # 36 tests : API HTTP, persistance, régressions + 4 audits
```
Les audits historiques restent exécutables individuellement :
```bash
python build1_2_audit.py    # Core Domain + Run Engine  (14 tests, 100 samples)
python build12_audit.py     # API service layer          (9 tests, 100 samples)
python build13_audit.py     # Persistance + WODs          (9 tests, 100 samples)
python build14_audit.py     # RCOS                        (9 tests, 100 samples)
```
Les audits B8-B11 sont dans leurs dossiers de build respectifs (historique).

## CI/CD
Les workflows sont à la racine du dépôt (`.github/workflows/`) : pytest + audits,
validation PostgreSQL+Redis, build Docker + smoke test — à chaque push.

## Endpoints (21)
**Moteurs (13)** :
/health · /coach/daily-decision · /coach/weekly-budget · /coach/arbitrate-goals ·
/run/hr-profile · /run/predictions · /run/pace-table · /strength/generate ·
/strength/pr-estimate · /raid/strength-report · /plans/auto-generate ·
/nutrition/daily-macros · /nutrition/selection-day

**Séance & planning (3)** :
POST /coach/session (décision + séance détaillée, calée sur le planning 3/2/2/3) ·
POST /schedule/day · POST /schedule/week

**Persistance (5)** — utilisés par l'app mobile (file de sync offline) :
POST /metrics/record · POST /sessions/complete · POST /benchmarks/record ·
GET /metrics/latest · GET /benchmarks/{id}/progression

La base est SQLite par défaut (`RAID_COACH_DB`, défaut `data/raid_coach.db`),
PostgreSQL/Redis en production.

## État
Backend 100% (B1→B14) + persistance branchée à l'API. App iOS : `../mobile`.
