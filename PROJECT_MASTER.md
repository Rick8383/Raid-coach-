# PROJECT MASTER

> RAID Coach Elite+ · Source de vérité unique du projet
> Version 2.4 · 12 juin 2026

-----

## 1. Vision du projet

### Objectif principal

Développer une application de coaching adaptatif de qualité professionnelle permettant à l’athlète (le porteur du projet) de **réussir les tests de sélection RAID** en fonction de son niveau actuel, via un moteur décisionnel intelligent pilotant l’intégralité de sa préparation physique.

### Objectifs secondaires

- Application iPhone en priorité, Android à plus long terme
- Beta exploitable très évoluée avant l’interface finale (“le moteur avant le corps”)
- Produit unique sur le marché — aucune app existante ne combine Run + CrossFit + Strength + Nutrition pilotés par un Adaptive Coach central orienté RAID
- Qualité professionnelle à tous les niveaux (code, architecture, validation)

### Valeur métier

- Préparation RAID complète et personnalisée sans coach humain
- Adaptation quotidienne automatique (fatigue, récupération, contraintes de vie)
- Prédiction de réussite des objectifs

-----

## 2. Résumé exécutif

RAID Coach Elite+ est une plateforme de coaching adaptatif combinant 4 moteurs d’entraînement (Run, CrossFit, Hyrox, Strength), un moteur nutrition, et une couche d’intelligence décisionnelle (Adaptive Coach) qui pilote la progression de l’athlète jusqu’aux tests RAID. Le projet a été initié avec ChatGPT, a produit un prototype PWA fonctionnel (V8.4.7) et 7 builds de moteurs Python validés (B3→B7). Le développement continue désormais avec Claude. La stratégie actuelle : **finaliser intégralement le backend/moteur avant de construire l’interface mobile**.

-----

## 3. État actuel

### Phase en cours

**Phase 4 — App iOS** · v1 beta livrée, prochaines itérations : écrans séance détaillée, calendrier, nutrition, saisie benchmarks
**PHASES 1-2-3 TERMINÉES ✅ — LE MOTEUR EST COMPLET (B3→B14)** — Prochain : **Phase 4 — App mobile React Native iOS** (ou BUILD 15 intelligence prédictive)

### Dernière mise à jour

11 juin 2026 — Création du PROJECT_MASTER.md, consolidation de tout l’historique ChatGPT, validation du Master Plan Backend.

### Avancement global

```
Vision & Architecture          ██████████████  100 %
Moteurs Python (B3→B7)         ████████████░░   85 %
Prototype PWA (V8.4.7)         ████████░░░░░░   60 % (utilisable, dette technique)
Moteurs manquants (B8-B11)     ██████████████  100 % (B8 ✅ B9 ✅ B10 ✅ B11 ✅)
API REST (B12)                 ██████████████  100 % ✅
Base de données (B13)          ██████████████  100 % ✅
RCOS / Memory (B14)            ██████████████  100 % ✅
Intelligence prédictive (B15)  ░░░░░░░░░░░░░░    0 %
App mobile iOS                 ██████░░░░░░░░   40 % (v1 beta : 3 écrans cœur)

Projet global vers beta exploitable : ≈ 45 %
```

-----

## 4. Architecture

### Architecture fonctionnelle

```
Athlète → Entraînement → Historique → Analytics → Adaptive Coach → Nouvelle séance optimisée
```

Boucle d’apprentissage continue : le système devient plus intelligent après chaque entraînement.

### Architecture technique

```
┌─────────────────────────────────┐
│   App iOS (React Native Expo)   │  ← Phase 4 (plus tard)
│   PWA V8.4.7 (provisoire)       │  ← Utilisable aujourd'hui
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│   API FastAPI (Python)          │  ← BUILD 12
│   Auth JWT · Swagger auto       │
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│   Moteurs Python (engines/)     │  ← B3→B11
│   Run · CrossFit · Hyrox ·      │
│   Strength · Nutrition ·        │
│   Adaptive · Analytics · Plans  │
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│   PostgreSQL + Redis            │  ← BUILD 13
└─────────────────────────────────┘
```

### Infrastructure

- Docker pour la conteneurisation
- Railway ou Render pour le déploiement beta (K8s seulement si montée en charge)
- Monitoring : Sentry dès la beta ; Grafana + Prometheus plus tard

### Déploiement

- CI/CD : GitHub Actions (workflows existants B3→B7 à étendre)
- GitLab CI configuré en fallback
- Repo GitHub **privé** avec squash merges (discrétion souhaitée)

### Technologies utilisées

|Couche |Techno                           |Statut              |
|-------|---------------------------------|--------------------|
|Moteurs|Python 3.12, dataclasses         |✅ En place          |
|API    |FastAPI + Pydantic               |📋 À construire (B12)|
|BDD    |PostgreSQL + SQLAlchemy + Alembic|📋 À construire (B13)|
|Cache  |Redis                            |📋 À construire (B13)|
|Mobile |React Native (Expo) — iOS first  |📋 Phase 4           |
|Tests  |pytest, audits 100 samples       |✅ Standard établi   |

-----

## 5. Décisions validées

|Date      |Décision                                                   |Justification                                                                           |
|----------|-----------------------------------------------------------|----------------------------------------------------------------------------------------|
|2026-06-08|Architecture cible définie (Engineering Context)           |Document de référence rédigé par ChatGPT sur prompt utilisateur                         |
|2026-06-10|Consolidation B3+B4+B5 en un seul bloc, peu de commits     |Discrétion sur le nouveau compte GitHub                                                 |
|2026-06-11|Migration du projet de ChatGPT vers Claude                 |Continuité assurée via fichiers + PROJECT_MASTER.md                                     |
|2026-06-11|**FastAPI remplace NestJS** pour le backend API            |4 500 lignes Python validées — réécriture TypeScript = risque et perte de temps inutiles|
|2026-06-11|**React Native (Expo) remplace Next.js PWA** pour le mobile|Cible iPhone natif demandée, Android ensuite sans réécriture                            |
|2026-06-11|**Moteur d’abord, interface ensuite**                      |Priorité utilisateur : un cœur complet avant le corps                                   |
|2026-06-11|**Rester sur GitHub** (repo privé)                         |Workflows existants, GitLab en fallback déjà prêt                                       |
|2026-06-11|PWA V8.4.7 conservée comme app provisoire                  |Continuité de l’entraînement pendant le développement                                   |
|2026-06-11|PROJECT_MASTER.md = source de vérité unique                |Pallier la non-persistance mémoire entre conversations IA                               |

-----

## 6. Contraintes

### Contraintes métier

- L’app doit permettre la réussite des tests de sélection RAID de l’utilisateur (enjeu personnel réel)
- Le coach ne doit JAMAIS générer une séance dangereuse (garde-fous obligatoires)
- Utilisation terrain : salle, piste, forêt, montagne → offline obligatoire à terme

### Contraintes techniques

- Génération séance < 300 ms · Dashboard < 500 ms · Navigation < 100 ms
- Scalabilité 10 000 → 1 000 000 users sans refonte majeure
- Disponibilité 99,9 %
- Sécurité : JWT + Refresh Token, TLS, bcrypt/argon2
- Standard de validation : 100 samples / 0 exception / audit PASS pour chaque build

### Contraintes légales

- RGPD à prévoir si ouverture à d’autres utilisateurs (données de santé)

### Contraintes budgétaires

- Non formalisées. Choix actuels orientés coût minimal (Railway/Render vs K8s).

-----

## 7. Fonctionnalités

### Terminées (moteurs Python validés)

- ✅ B3 — Universal Training Core + CrossFit (50 familles) + Hyrox + Running (25 familles)
- ✅ B4A — Adaptive Programming Engine (PROGRESS/MAINTAIN/DELOAD/RECOVER)
- ✅ B4B — Periodization Engine
- ✅ B4C — Readiness Engine (GREEN/YELLOW/ORANGE/RED)
- ✅ B4D — Recovery Engine (OPTIMAL→CRITICAL)
- ✅ B4E — Session Governor (ALLOW/REDUCE/MODIFY/BLOCK)
- ✅ B5 — Road To RAID complet (Profiler, Score, Weakness, Gap, Periodization, Plans 8-24 sem.)
- ✅ B6 — Analytics Engine (7 scores : fitness, fatigue, readiness, risk, performance, trends, weakness)
- ✅ B7 — Auto Plan Generator (goal ingestion → plans complets avec règles adaptatives)

### Terminées (PWA uniquement — à porter en Python)

- ✅ Strength Engine Elite+ (PR Engine, périodisation, méthodes avancées) — PWA seulement
- ✅ Nutrition (macros adaptatives, plans repas) — PWA seulement
- ✅ Calendrier (vue mensuelle, export iCal) — PWA seulement
- ✅ HR Zones + Run Predictions + tableau allures — PWA seulement

### En cours

- 🚧 Rien en cours — prochain : BUILD 8

### Planifiées (ordre d’exécution)

1. ✅ BUILD 8 — Strength Engine Python — VALIDÉ 11/06 (60 familles, 360 templates, 7 tests PASS, audit 100 samples PASS)
1. ✅ BUILD 9 — Run Completions — VALIDÉ 11/06 (HR Zones Tanaka/Karvonen, Prédictions Riegel, Pace Calculator terrain/D+/charge, bibliothèque 110 familles dont WODs spécifiques sélection)
1. ✅ BUILD 10 — Coach Brain — VALIDÉ 11/06 (Fatigue Budget calibré 3/2/2/3, ACWR Gabbett, Goal Arbitration avec plancher RAID 30%, Daily Decision avec règles sciatique L5-S1)
1. ✅ BUILD 11 — Nutrition Engine — VALIDÉ 11/06 (Mifflin/Katch-McArdle, cyclage glucidique calé sur jours OFF/travaillés, phase RECOMP active 75→79kg, plan jour de sélection, suppléments evidence-based clean)
1. ✅ BUILD 12 — API FastAPI — VALIDÉ 11/06 (13 endpoints, couche service 9/9 tests + 100 samples PASS, Dockerfile, workflow CI live-test, repo backend consolidé 129 fichiers)
1. ✅ BUILD 13 — Persistance — VALIDÉ 11/06 (schéma 10 tables, 7 repositories, cache Redis-compatible, CI PostgreSQL+Redis fournie) + module WODs Sélection officiels (2 benchmarks réels + générateur de variantes)
1. ✅ BUILD 14 — RCOS — VALIDÉ 11/06 (Athlete Memory avec oubli différencié, Digital Twin Banister CTL/ATL/TSB + projection taper, Life Engine, Annual Planner rétro-planning 140 sem avec cycles Base/Build/Peak + benchmarks officiels tous les ~14 sem, Best Action Today)
1. 🚧 Phase 4 — App iOS v1 BETA LIVRÉE 11/06 (React Native Expo : Check-in 30s, Best Action Today + compte à rebours sélection, Objectifs élite avec progression ; client API offline-first cache+sync queue ; design system ‘opérationnel nocturne’ signature liseré readiness ; TypeScript validé)
1. 📋 BUILD 15 — Personal Performance Intelligence (prédiction performance, blessures, probabilité de réussite)

### Abandonnées

- ❌ Stack NestJS/TypeScript (remplacée par FastAPI — décision 2026-06-11)
- ❌ Next.js PWA comme frontend cible (remplacé par React Native — décision 2026-06-11)
- ❌ Kubernetes pour la beta (reporté — Railway/Render suffisent)

-----

## 8. Backlog priorisé

|Priorité|Tâche                                  |Statut                                |
|--------|---------------------------------------|--------------------------------------|
|P0      |BUILD 8 — Strength Engine Python       |✅ VALIDÉ                              |
|P0      |BUILD 9 — Run Completions              |✅ VALIDÉ                              |
|P0      |BUILD 10 — Coach Brain                 |✅ VALIDÉ                              |
|P1      |BUILD 12 — API FastAPI                 |✅ VALIDÉ                              |
|P1      |BUILD 13 — Persistance PostgreSQL/Redis|✅ VALIDÉ                              |
|P1      |Consolidation repo GitHub privé unique |📋 En attente                          |
|P2      |BUILD 11 — Nutrition Engine            |✅ VALIDÉ                              |
|P2      |BUILD 14 — RCOS / Athlete Memory       |✅ VALIDÉ                              |
|P3      |App mobile React Native iOS            |🚧 v1 beta livrée — à tester sur iPhone|
|P3      |BUILD 15 — Intelligence prédictive     |📋 Long terme                          |

-----

## 9. Risques

|Risque                                                       |Impact|Probabilité|Action                                                             |
|-------------------------------------------------------------|------|-----------|-------------------------------------------------------------------|
|Explosion complexité moteur Run (1000+ séances)              |Élevé |Moyenne    |Génération paramétrique, pas de stockage manuel                    |
|Séances incohérentes générées                                |Élevé |Moyenne    |Workout Validator avant affichage                                  |
|Adaptive Coach erratique (peu d’historique)                  |Élevé |Élevée     |Règles métier fixes + couche adaptive ; jamais de séance dangereuse|
|Dette technique PWA monolithique (263 Ko index.html)         |Moyen |Certaine   |PWA = provisoire ; remplacée en Phase 4                            |
|Perte de contexte entre conversations IA                     |Élevé |Certaine   |PROJECT_MASTER.md + repo GitHub = sources de vérité                |
|Fragilité fusions multi-IA (ChatGPT/Grok) dans la PWA        |Moyen |Certaine   |Ne plus faire évoluer la PWA ; figer en l’état                     |
|Écart entre moteurs Python et logique PWA (2 implémentations)|Moyen |Élevée     |Python = référence unique ; PWA jetée à terme                      |
|Compte GitHub : discrétion souhaitée                         |Faible|—          |Repo privé, squash merges, peu de workflows visibles               |

-----

## 10. Problèmes ouverts

1. **Export ChatGPT en attente** — l’export complet des conversations (conversations.json) peut prendre quelques jours. À analyser dès réception pour récupérer d’éventuels détails manqués.
1. **Profil athlète réel non documenté** — niveau actuel, FCmax, VMA, PRs force, date cible des tests RAID, nature exacte des tests de sélection. Nécessaire pour calibrer les moteurs (notamment B8 Road To RAID Strength et B9 predictions).
1. **Définition précise des “tests RAID”** — quelles épreuves exactement (tractions ? portage ? course chronométrée ? parcours ?). Impacte directement les objectifs des moteurs.
1. **Divergence bibliothèque Run** — roadmap originale annonce 110 familles / 660 templates, le code actuel en contient 25. À combler en BUILD 9 ou à réviser l’objectif.

-----

## 11. Base de connaissances

### Métier

- RAID = épreuves combinant endurance, montagne, portage, vitesse, technique
- 5 dimensions évaluées par le RAID Profiler : endurance, mountain, carry, speed, technical
- Niveaux athlète : foundation → base → build → ready
- Périodisation : Base / Build / Peak / Taper / Race
- Phases force : Accumulation / Intensification / Peaking / Test / Deload

### Technique

- Standard de validation établi : 100 samples, 0 exception, audit PASS, rapport JSON + page HTML
- Pattern moteur établi : models.py (dataclasses frozen) → registry → template_factory → generator → service
- Pattern décisionnel établi : Input.validate() → règles hiérarchiques → Output.validate()
- Convention : chaque build a son audit (.py), son report (.json), sa page de statut (.html), son workflow (.yml)

### Processus

- Builds séquentiels avec validation avant fermeture (“BUILD X CLOSED/VALIDATED”)
- Consolidations régulières en ZIP (“Ultimate Consolidation”)
- Manifests JSON à chaque consolidation

### Références

- Engineering Context complet (fourni le 11/06/2026 — architecture, contraintes, data flow, risques)
- Roadmap B1→B9 originale (fournie le 11/06/2026)
- Master Plan Backend v2.0 (généré le 11/06/2026 — fichier RAID_Coach_Master_Plan_Backend.md)

-----

## 12. Fichiers analysés

|Fichier                                             |Date      |Résumé                                                                                                             |
|----------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------|
|Raid_Coach_Ultimate_Consolidation_v1_6_Build7.zip   |11/06/2026|Consolidation complète B1→B7, 207 fichiers, moteurs Python + audits + workflows                                    |
|Roadmap complète (document collé)                   |11/06/2026|Cartographie B1→B9 avec statuts ; révèle B1 (backend/BDD) jamais réalisé                                           |
|Raid_Coach_Build4_Final_Validation.zip              |11/06/2026|B4 CLOSED — 25 tests PASS, 5 moteurs adaptatifs validés                                                            |
|Raid_Coach_Build5A_RAID_Profiler_Validation.zip     |11/06/2026|Profiler 5 dimensions, 100 samples PASS                                                                            |
|Raid_Coach_Build5_Road_To_RAID_Validation.zip       |11/06/2026|Pipeline complet plans RAID 8-24 semaines, PASS                                                                    |
|Raid_Coach_Build6_Analytics_Engine_Validation.zip   |11/06/2026|7 scores analytics, PASS                                                                                           |
|Raid_Coach_Build7_Auto_Plan_Generator_Validation.zip|11/06/2026|Génération plans 4 types d’objectifs, PASS                                                                         |
|RAID_Coach_Context_Engineering_Markdown.zip         |11/06/2026|9 fiches markdown vision produit (modules, data model, roadmap V8/V9)                                              |
|Engineering Context complet (document collé)        |11/06/2026|Architecture cible, stack, contraintes perfs, data flow, 5 risques + mitigations                                   |
|RAID_Coach_V8_4_7_NEXT_STEP.zip                     |11/06/2026|PWA monolithique 263 Ko — app provisoire utilisable ; révèle Strength/Nutrition/Calendar/HR Zones absents du Python|
|Prompt Système Mémoire Persistante (document collé) |11/06/2026|Méthodologie PROJECT_MASTER.md appliquée — ce document en est le résultat                                          |

-----

## 13. Historique des changements

|Date      |Changement                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|2026-06-08|[ChatGPT] V8.4.7 NEXT STEP — dernière version PWA livrée                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|2026-06-10|[ChatGPT] Mega Consolidation B1→B5                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|2026-06-11|[ChatGPT] Validations B5A, B5, B6, B7 + Ultimate Consolidation Build 7                                                                                                                                                                                                                                                                                                                                                                                                                        |
|2026-06-11|[Claude] Reprise du projet — analyse des 8 ZIPs + 3 documents                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|2026-06-11|[Claude] Récap complet généré (RAID_Coach_Recap_Complet.md)                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|2026-06-11|[Claude] Décisions stack : FastAPI, React Native, GitHub privé                                                                                                                                                                                                                                                                                                                                                                                                                                |
|2026-06-11|[Claude] Master Plan Backend v2.0 généré (Builds 8→15 détaillés)                                                                                                                                                                                                                                                                                                                                                                                                                              |
|2026-06-11|[Claude] PROJECT_MASTER.md v1.0 créé — source de vérité instaurée                                                                                                                                                                                                                                                                                                                                                                                                                             |
|2026-06-11|[Claude] Recherche web : épreuves sélection RAID documentées (section 15)                                                                                                                                                                                                                                                                                                                                                                                                                     |
|2026-06-11|[Claude] Profil athlète réel enregistré : DC 95 / tractions 16 / squat 110 / 8km 40min                                                                                                                                                                                                                                                                                                                                                                                                        |
|2026-06-11|[Claude] Horizon fixé : sélection 2029-2030 (4 ans)                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|2026-06-11|[Claude] BUILD 8 Strength Engine développé, testé (7/7 PASS) et audité (100 samples, 0 exception, PASS)                                                                                                                                                                                                                                                                                                                                                                                       |
|2026-06-11|[Claude] Rôle Claude : co-fondateur technique, automatisation max, utilisateur seul décisionnaire                                                                                                                                                                                                                                                                                                                                                                                             |
|2026-06-11|[Claude] Objectifs élite top 5% enregistrés (50 tractions, 150 pompes, 60 dips, 80 T2B, Cooper 4000) — tier elite ajouté au moteur B8                                                                                                                                                                                                                                                                                                                                                         |
|2026-06-11|[Claude] BUILD 9 Run Completions développé et validé (4/4 tests, audit 100 samples PASS) — VMA athlète estimée 13,6 km/h, Cooper estimé ~2580m, VMA cible Cooper 4000m = 21 km/h                                                                                                                                                                                                                                                                                                              |
|2026-06-11|[Claude] Profil athlète COMPLET enregistré : ex-1er RPIMa, policier 1 an, 31 ans, 75kg, readiness PASS 86% / ELITE 47%                                                                                                                                                                                                                                                                                                                                                                        |
|2026-06-11|[Claude] ⚠️ Alerte limite d’âge émise : fenêtre réelle probable 2028-2029 (limite 35 ans GPX / 38 officiers) — décision utilisateur attendue                                                                                                                                                                                                                                                                                                                                                   |
|2026-06-11|[Claude] Contrainte sciatique L5-S1 intégrée comme règle de sécurité permanente                                                                                                                                                                                                                                                                                                                                                                                                               |
|2026-06-11|[DÉCISION USER] Cooper cible élite révisé : 4000m → 3200m (VMA requise 16,8 km/h, aligné avec objectif semi 4:30/km) — moteur B8 recalibré, audit re-PASS                                                                                                                                                                                                                                                                                                                                     |
|2026-06-11|[DÉCISION USER] Cibles élite révisées : tractions 50→35, pompes 150→120 — readiness élite 52,7%                                                                                                                                                                                                                                                                                                                                                                                               |
|2026-06-11|[RÉSOLU] Limite d’âge : né 30/07/1995, GPX → fenêtre officielle 2028-2029, périodisation calée sur 2029                                                                                                                                                                                                                                                                                                                                                                                       |
|2026-06-11|[Claude] BUILD 10 Coach Brain validé (7/7 tests, 100 samples PASS) : budgets fatigue grande semaine 420 SU / petite 620 SU, ACWR, arbitrage objectifs, décision quotidienne calée sur rythme police et sciatique                                                                                                                                                                                                                                                                              |
|2026-06-11|[Claude] BUILD 11 Nutrition Engine validé (7/7 tests, 100 samples PASS) : recomp 2,2g/kg protéines, cyclage glucides, plan nutrition jour de sélection, suppléments clean — PHASE 1 TERMINÉE                                                                                                                                                                                                                                                                                                  |
|2026-06-11|[USER] WODs officiels sélection RAID 2026 fournis : WOD PDC (death by EMOM+1 : 11 cal ski/box over/row/tractions/burpees target) + WOD Force (time cap 5min lesté : echo bike, trap bar 115kg, farmer walk, box over bélier, max distance mannequin)                                                                                                                                                                                                                                          |
|2026-06-11|[DÉCISION USER] Standards matériels validés : gilet 10kg, gilet lourd 20kg, bélier 16kg, mannequin 75kg, trap bar DL 115kg                                                                                                                                                                                                                                                                                                                                                                    |
|2026-06-11|[Claude] BUILD 13 Persistance validé (9/9 tests, 100 samples PASS) : 10 tables (athlète, sessions, métriques, PRs, benchmarks, plans, décisions coach, nutrition), 7 repositories, cache TTL, CI PostgreSQL+Redis. Module selection_wods.py : 2 benchmarks officiels trackés + générateur de variantes ADN sélection + blocs de progression 4-16 sem avec baseline/re-test — PHASE 2 TERMINÉE                                                                                                 |
|2026-06-12|[Claude] ZIPs finaux consolidés : Raid_Coach_Backend_Complete_B1_B14.zip (169 fichiers, tous moteurs + API + BDD) et Raid_Coach_App_iOS_v1_Beta.zip (21 fichiers) + guide SETUP_GITHUB_CLAUDE_CODE.md — prêts pour push GitHub et reprise sous Claude Code                                                                                                                                                                                                                                    |
|2026-06-12|[Claude] BUILD 1+2 construits et validés depuis les fichiers sources uploadés (Structure_build1.md, Build2.x, Test_Build2.zip) : Build 1 = Core Domain (Athlete, Goal, Session, SessionResult, DailyMetrics, PerformanceSnapshot, RaidProfile, AthleteMemory + ReadinessEngine/FatigueEngine/RaidProfileEngine), Build 2 = Run Engine Runtime (110 familles, 660 templates, pipeline 8 moteurs : selector/modifier/governor/terrain/raid/anti-repetition) — 14/14 tests PASS, 100 samples PASS|
|2026-06-11|[Claude] Phase 4 démarrée : app iOS v1 beta livrée (Expo/React Native, 3 écrans cœur, offline-first, design ‘opérationnel nocturne’). Étapes user : npm install + expo start –ios, puis TestFlight via EAS (compte Apple Developer 99$/an)                                                                                                                                                                                                                                                    |
|2026-06-11|[Claude] BUILD 14 RCOS validé (9/9 tests, 100 samples PASS) : mémoire athlète (signaux blessure quasi-permanents, decay différencié), Digital Twin Banister, Life Engine multiplicatif, Annual Planner rétro 2029 (40 blocs, 10 jalons benchmarks), Best Action Today intégrant tout — MOTEUR COMPLET                                                                                                                                                                                         |
|2026-06-11|[Claude] BUILD 12 API validé (9/9 tests, 100 samples PASS) : façade CoachAPI sur 13 moteurs, 13 endpoints FastAPI, structure repo finale consolidée (engines/ + legacy B3-B7 + api/), Dockerfile + CI live-test fourni. Note : exécution FastAPI réelle à confirmer au 1er push GitHub (sandbox sans réseau)                                                                                                                                                                                  |

-----

## 14. Prochaines actions recommandées

1. **🔴 P0 — Documenter le profil athlète réel** : niveau actuel, date des tests RAID, nature des épreuves, PRs actuels, FCmax/VMA. → Indispensable pour calibrer les moteurs sur TES objectifs (c’est le but final du projet).
1. **🔴 P0 — Lancer BUILD 8 (Strength Engine Python)** : le plus gros manque du backend.
1. **🔴 P0 — Enchaîner BUILD 9 puis BUILD 10** : compléter le cerveau du coach.
1. **🟡 P1 — Créer le repo GitHub privé consolidé** avec la structure cible (engines/, api/, db/, tests/) et y pousser PROJECT_MASTER.md à la racine.
1. **🟡 P1 — Analyser l’export ChatGPT** dès réception pour vérifier qu’aucune information n’a été perdue.
1. **🟢 P2 — Mettre à jour PROJECT_MASTER.md après chaque build** (mode “Met à jour la mémoire projet”).

-----

-----

## 15. Profil Athlète & Objectif RAID (données réelles)

### Objectif

**Sélection RAID (unité d’élite Police nationale)** — **FENÊTRE OFFICIELLE : 2028-2029** (verrouillée le 11/06/2026).
Né le 30/07/1995, gardien de la paix : 34 ans au 31/12/2029 (dernière année éligible), 35 ans au 31/12/2030 (trop tard).
Éligible dès 2028 (3 ans d’ancienneté). **Plan de préparation : ~2,5 à 3,5 ans.**
Stratégie : viser 2029 comme année principale, 2028 comme option si progression exceptionnelle.
Parcours requis : concours Police nationale → 3 ans d’ancienneté minimum → candidature RAID (< 35 ans gardien de la paix / < 38 ans officier).

### Épreuves de sélection RAID (recherche web 11/06/2026 — à confirmer/compléter par l’utilisateur)

**Présélection (1 journée)** : enchaînement de mouvements de musculation au poids de corps avec minimas.
**Semaine de sélection** (varie chaque année) :

- 2 montées de corde 5 m (sans contrainte de temps, gestes analysés)
- Pompes jusqu’à épuisement
- Tractions, répulsions (dips), relevés de jambes jusqu’à épuisement
- Endurance : test Cooper (12 min) + sprint 50 m
- Natation : 50 m vitesse, 25 m apnée, évacuation mannequin immergé, plongeon avec gilet 50 kg
- Sports de combat, tir, ball-trap
- Épreuves psychologiques : tunnel obscur, vertige, claustrophobie, simulation tuerie de masse

### Profil actuel COMPLET (mis à jour 11/06/2026)

|Donnée              |Valeur                                                               |
|--------------------|---------------------------------------------------------------------|
|Âge / Taille / Poids|31 ans · 172 cm · 75 kg (objectif : 78-80 kg sec, -3-5 kg gras)      |
|Parcours            |**Ex-militaire 1er RPIMa Bayonne (4 ans)** · **Policier depuis 1 an**|
|DC 1RM              |95 kg (ratio 1.27)                                                   |
|Squat 1RM           |110 kg (ratio 1.47)                                                  |
|Deadlift 1RM        |150 kg ⚠️ sciatique L5-S1 à gérer                                     |
|Tractions max       |16                                                                   |
|Pompes max          |~60                                                                  |
|Dips max            |~40                                                                  |
|Toes to bar max     |18                                                                   |
|Corde 5 m           |technique acquise (avec jambes), consécutif à déterminer             |
|Cooper              |3 100 m (époque RPIMa) · ~2 850 m estimé actuel                      |
|8 km                |40 min (5:00/km) · VMA estimée 13,6 km/h                             |
|FCmax               |à tester · Tanaka estimé 186 bpm                                     |
|Natation            |à l’aise · apnée 25 m OK · 50 m jamais chronométré                   |
|Objectif perso semi |4:30/km (1h35) → VMA requise ~16 km/h                                |

### Readiness calculée (moteur B8, données réelles, 75 kg)

- **Tier PASS (passage confortable) : 86 % — focus : montées de corde, ~10 semaines de travail ciblé**
- **Tier ELITE (top 5%) : 52,7 % — focus : toes to bar (18/80), corde (1/4), tractions (16/35), pompes (60/120)**

### Contraintes & ressources

- **Rythme pro police 3/2/2/3** : grande semaine travaillée lun/mar/ven/sam/dim ; petite semaine travaillée mer/jeu
- Jours OFF : run le matin + muscu/WOD le soir, ou séance CrossFit complète (haltéro-gym-wod)
- Natation le dimanche en récup (petites semaines)
- Accès complet : salle muscu, box CrossFit, piscine, corde, piste
- ⚠️ **Sciatique L5-S1** (gêne > douleur) : adapter deadlift/squat lourd, gainage anti-flexion prioritaire, éviter flexion lombaire chargée en fatigue

### ✅ LIMITE D’ÂGE — RÉSOLU (11/06/2026)

Naissance 30/07/1995, GPX → dernière année possible **2029**. Fenêtre confirmée **2028-2029**. Périodisation calée sur sélection 2029 (option 2028).

### Données encore manquantes

- Montées de corde consécutives (à tester)
- FCmax réelle + Cooper réel (tests à planifier en semaine 1 du plan)
- 50 m nage chrono

### Objectifs cibles ÉLITE (top 5% des candidats — définis par l’utilisateur le 11/06/2026)

|Épreuve    |Cible élite               |Actuel         |
|-----------|--------------------------|---------------|
|Tractions  |**35** (révisé 11/06)     |16             |
|Pompes     |**120** (révisé 11/06)    |~60            |
|Dips       |60                        |~40            |
|Toes to bar|80                        |18             |
|Cooper     |**3 200 m** (révisé 11/06)|~2 850 m estimé|

Readiness élite actuelle : **52,7 %** (cibles révisées : 35 tractions, 120 pompes, Cooper 3200). Le moteur B8 gère désormais 2 barèmes : tier “pass” (passage confortable) et tier “elite” (top 5%).
✅ FAIT : WODs officiels sélection 2026 intégrés (engines/selection_wods.py) — benchmarks de référence à re-tester toutes les 8-12 semaines.

*PROJECT_MASTER.md v2.4 · Maintenu par Claude · Toute nouvelle conversation doit commencer par “Charge PROJECT_MASTER.md” avec ce fichier joint.*

-----

## 16. Reprise sous Claude Code — Backend déployable + App exploitable (13/06/2026)

> Ajout du 13/06/2026. Ce paragraphe complète l'historique ci-dessus sans rien en modifier.

Le projet a été repris sous **Claude Code** et structuré en monorepo (`backend/` FastAPI + moteurs, `mobile/` Expo/React Native, `PROJECT_MASTER.md` à la racine).

**Audit & fiabilité** — Les fichiers backend (B1→B14) et l'app iOS ont été importés, audités et rendus exécutables de bout en bout. **9 bugs confirmés corrigés** (avec tests de régression) : connexion SQLite inutilisable depuis le threadpool FastAPI, readiness `run_engine` à signe inversé, import `run_elite` via `/tmp`, macros nutrition sur profils extrêmes, 500 sur payloads imbriqués, singularité Brzycki e1RM, `raid_plan` cassé, injection SQL latente (allowlist colonnes), récursion non bornée des variantes WOD. Un test d'audit non déterministe (variété run) a été figé par seed.

**Backend (34 endpoints)** — Générateur de séance **par discipline** (`/generate` : course / force / WOD, indépendant de la décision du jour et de la montre, variété par seed) ; **planning police 3/2/2/3** source de vérité (ancre : semaine du **lundi 15/06/2026 = grande semaine**, alternance) ; agenda prévisionnel, analytics (forme/fatigue/ACWR/risque), **roadmap annuel RCOS** rétro-planifié jusqu'à 2029 ; **persistance des séances générées** (planifiées/faites → historique + agenda). **Boucle adaptative fermée** : RPE ressenti → charge (SU) → l'historique (disciplines récentes, budget fatigue hebdo, jours sans repos, ACWR) ré-alimente la décision quotidienne.

**Montre & Garmin** — Couche wearable (HRV / FC repos / sommeil) alimentant le check-in et le plan ; **intégration Garmin Connect OAuth 1.0a côté serveur** (`/garmin/*`, table `garmin_tokens`, mapping Wellness API → métriques) qui s'active avec les clés `GARMIN_CONSUMER_KEY/SECRET`, sans incidence sur les boutons « Générer ».

**App mobile** — Écrans : check-in, jour, séance détaillée, séances Course/Force/WOD, agenda, nutrition, objectifs, profil (+ roadmap + connexion montre + rappels). **Compatibilité web** rétablie (curseurs natifs remplacés ; `expo export --platform web` OK). **Rappels locaux** (check-in du matin + re-test benchmarks). Config **EAS/TestFlight** fournie (`eas.json`, `app.json`).

**Déploiement** — Dockerfile (port `$PORT` dynamique), CORS, **blueprint Render `render.yaml`**, guide `DEPLOY.md`. ⚠️ **Plan Render FREE** : les disques persistants n'y sont pas supportés (erreur *« disks are not supported for free tier services »*) → bloc `disk:` retiré du `render.yaml` le 13/06/2026, déploiement OK. Conséquence : la base SQLite (`/app/data`) est **éphémère** (remise à zéro à chaque redéploiement/réveil). Pour conserver les données : plan payant + `disk:`, ou base **PostgreSQL externe** (`DATABASE_URL`).

**Validation** — 74 tests pytest + 4 audits 100 samples PASS, TypeScript strict 0 erreur, export web OK, CORS et endpoints vérifiés en live.

**Reste à la charge de l'utilisateur (comptes requis)** : déploiement backend (Render, fait — site en ligne), clés **Garmin Developer**, et **build EAS → TestFlight** (comptes Apple Developer + Expo) pour l'app iPhone.

*Addendum v2.5 · 13/06/2026 · Claude Code.*

-----

### Addendum v2.6 — Persistance PostgreSQL (13/06/2026)

> Complément à la section 16, sans rien y modifier.

Le plan **Render free** ne supporte pas les disques persistants : la base SQLite y était **éphémère** (réinitialisée à chaque redéploiement). La couche base de données est désormais **bi-backend** (`backend/db/database.py`) : **SQLite** par défaut (local, tests) et **PostgreSQL** dès que `DATABASE_URL` est défini (production). Le SQL des repositories est inchangé (`?` traduits en `%s`, DDL canonique traduit en SERIAL/TIMESTAMPTZ, `RETURNING id` pour les insertions), via un pool de connexions thread-safe. Le `render.yaml` provisionne une base PostgreSQL et injecte `DATABASE_URL` → **données persistantes** (athlète, métriques, séances, historique, tokens Garmin) sans disque payant ; alternative externe gratuite (Neon/Supabase) documentée dans `DEPLOY.md`. Schéma créé au démarrage, aucune migration manuelle. Validation : 74 pytest + 3 tests de traduction PG (intégration end-to-end exécutée sur le job CI PostgreSQL), aucune régression sur le chemin SQLite.

*Addendum v2.6 · 13/06/2026 · Claude Code.*

-----

## 17. Mise à jour majeure du site — Contenu d'entraînement complet (14/06/2026)

> Ajout du 14/06/2026. Complète les sections précédentes sans rien y modifier.

### Ce qui a été implémenté
- **Plan annuel jusqu'à 2029** (`/plan/annual`, `backend/data/annual_plan.json`) : macro-périodisation BASE(6)/BUILD(5)/PEAK(2)/TRANSITION(1 deload), 141 semaines, 41 blocs avec dates/volumes SU/dominante, 11 jalons benchmarks officiels.
- **Plan glissant détaillé** (`/plan/weekly?from_week=&n=`) : N semaines jour par jour, chaque séance assemblée via les générateurs réels (course, force 5/3/1, WOD, natation), calée sur le 3/2/2/3 (jour OFF = double séance, service = séance courte, dimanche petite semaine = natation). Le 5/3/1 progresse avec le calendrier.
- **Générateur Run** (`/generate/run`, `/generate/run/library`) : 700 séances (100 × 7 types : vma_courte/longue, seuil, fartlek, tempo, z2, côtes), déterministe par seed (aucune répétition sur les 100 premières d'un type), allures km/h + min/km + %VMA et FC bpm + %FCmax depuis VMA 14 / FCmax 186 (surchargeables par le profil).
- **Générateur WOD** (`/generate/wod`, `/generate/wod/random`) : 15 formats, ~38 mouvements taggés (charges/distances FIXES), règles de cohérence (équilibre push/pull/legs/cardio, distances run/carry fixes), règle sciatique L5-S1 (`exclude_lumbar` ON par défaut → aucun mouvement lombaire, jamais en finisseur d'un WOD long).
- **Force 5/3/1** (`/generate/strength`, `/strength/cycle`) : TM DC 85 / Squat 100 / OHP 54 / Row 90, cycle 4 semaines (5/5/5+, 3/3/3+, 5/3/1+, deload), +2,5 kg haut / +5 kg bas par cycle, **Big 3 McGill** obligatoire en échauffement, accessoires double progression, **GtG tractions** (jour pull), deadlift lourd remplacé par hip thrust, **finisher WOD non lombaire**.
- **Interface** : onglet Séances (Course = 7 types + zones FC, Force = 5/3/1 Push/Pull/Legs, WOD = 15 formats + anti-lombaire), onglet Agenda avec bascule **Plan détaillé / Suivi** (calendrier glissant, jour → séances → détail dépliable). Sauvegarde des séances générées dans l'agenda. Compatibilité web conservée (`expo export --platform web` OK).

### Paramètres athlète utilisés
- VMA 14 km/h · FCmax 186 bpm · poids 75 kg
- 1RM DC 95 (TM 85) · 1RM Squat 110 (TM 100)
- Sciatique L5-S1 : `exclude_lumbar` ON par défaut sur les WOD, substitutions force
- Rythme police 3/2/2/3, ancre semaine du 15/06/2026 = grande semaine

### Validation
97 tests pytest + 4 audits 100 samples PASS (42 routes API), TypeScript strict 0 erreur, export web OK. Aucune régression sur les 9 bugs corrigés (addendum v2.5).

### À faire après cette mise à jour
- Saisir les vraies baselines (Cooper réel, FCmax test, montées de corde) → recalcul automatique des allures/charges.
- Tester le plan 2-3 semaines, saisir les RPE → la boucle adaptative ajuste.
- Build EAS → TestFlight (compte Apple Developer + Expo) pour l'iPhone.

*Addendum v2.7 (section 17) · 14/06/2026 · Claude Code.*

-----

### Addendum v2.8 — Finition « rendu pro » (14/06/2026)

> Complète la section 17 sans rien y modifier.

Rendu de séance **unifié et enrichi** : composants partagés `RunDetail` / `StrengthDetail` / `WodDetail` réutilisés par les générateurs **et** le plan détaillé — course avec zones FC colorées et allures multiples, force avec barres de charge par série, WOD structuré + note lombaire. **Graphes sans dépendance** (compatibles web) : composant `Chart` (BarChart, MeterBar avec zone « sweet spot » + marqueur, StackBar). Ajouts : **graphe de progression des charges** sur la page Force (`/strength/progression`, projection 6 cycles + 1RM estimé), **suivi chiffré des benchmarks** sur la page Objectifs (historique tracé + saisie d'un test du jour qui alimente le graphe), **jauges de charge** sur l'écran Jour (budget fatigue coloré par statut + ACWR avec zone optimale 0,8-1,3 et marqueur), **répartition visuelle des macros** sur la page Nutrition. Validation : 98 pytest + 4 audits PASS (43 routes), TypeScript strict 0 erreur, export web OK.

*Addendum v2.8 · 14/06/2026 · Claude Code.*

-----

### Addendum v2.9 — Déploiement web + corrections entraînement + moteur nutrition (15/06/2026)

> Complète les sections précédentes sans rien y modifier.

**Site en ligne** : frontend déployé sur **GitHub Pages** via workflow CI (`.github/workflows/deploy-web.yml`), URL **https://rick8383.github.io/Raid-coach-/** (base URL `/Raid-coach-` casse exacte du dépôt — un base URL en minuscules causait un écran blanc). Backend sur Render (`https://raid-coach-api.onrender.com`, CORS ouvert), auto-déployé sur push. Redéploiement auto à chaque push.

**Corrections entraînement** (vague 1) : Force 5/3/1 — Training Max relevés au niveau réel (DC 90 → 1RM ~100, objectif 140 ; Squat 105 → 1RM ~117, objectif 160 ; OHP 57,5 ; Row 92,5), deload remonté 50/60/70%, objectif 1RM affiché. WOD — L-sit retiré (plus d'exercice à temps fixe), reps cohérentes par bande (double-unders 20-100, et non 8), assault/echo/ski bike mis en avant, double-unders re-catégorisés « condi ». Course — permutation bijective de l'index : seeds consécutifs dispersés (fini 3×400→4×400→5×400…), unicité 100/type conservée.

**Moteur nutrition Elite+** (vague 2, `engines/nutrition_plus/`, evidence-based ISSN) : 10 compléments (créatine, collagène+vit C, whey, caséine, caféine, bêta-alanine, oméga-3, vit D3, magnésium, électrolytes) avec dose/timing/mécanisme/source/niveau de preuve ; 22 aliments (P/G/L/kcal /100g) ; convertisseur **macro→grammes** ; **garde-fous** lipides <0,8 g/kg, protéines <1,8 g/kg, RED-S (<25 kcal/kg FFM) ; planning compléments par type de séance ; 6 synergies + 6 anti-synergies. Endpoints `/nutrition/supplements|foods|synergies|portions|guardrails`. App : écran Nutrition à 4 onglets (Macros+garde-fous / Aliments→grammes / Compléments / Synergies).

**État** : 102 tests pytest + 4 audits 100 samples PASS (48 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v2.9 · 15/06/2026 · Claude Code.*

-----

### Addendum v3.0 — Coach Chat + chrono WOD compétition + tooltips RPE + fix agenda (16/06/2026)

> Complète les sections précédentes sans rien y modifier.

**Correctif bug « marquer comme fait » (Force → Agenda)** : quand plusieurs séances partagent une date (ex. footing planifié le matin + force marquée faite ensuite), l'agenda gardait la mauvaise (la plus ancienne écrasait la plus récente dans la construction du dict). `/agenda/week` priorise désormais une séance **`done`** sur une `planned`, et expose le **titre** de la séance retenue. Côté app, `saveSession` et `completeSession` **invalident le cache** `cache:agenda:*` / `cache:history` / `cache:analytics` après écriture → la séance se reflète immédiatement dans l'agenda (même hors ligne). Régression couverte par un test.

**Coach Chat (assistant déterministe, sans LLM externe)** : nouveau moteur `engines/coach_chat/` (offline-first, testable, aucune dépendance réseau) qui détecte l'intention par mots-clés pondérés (FR) et compose une réponse **personnalisée avec le profil réel** et le contexte du jour (planning 3/2/2/3, readiness/fatigue, semaines avant 2029). Couvre : séance du jour, planning, RPE, nutrition (macros/compléments/créatine), force 5/3/1 (charges/objectifs 1RM), course (allures/zones FC), WOD, sciatique L5-S1, sélection RAID, benchmarks, récupération. Endpoint `POST /coach/chat` (message + date optionnelle). App : **nouvel onglet COACH** (`CoachChatScreen`) — fil de discussion, rendu markdown léger (**gras**, listes), suggestions de relance cliquables.

**Chrono WOD qualité compétition** (`components/WodTimer.tsx` + `components/sound.ts`) : compte à rebours de départ **15 s par défaut** avec **bips 3-2-1 puis GO** (Web Audio API sur web, vibration de secours en natif — sans nouvelle dépendance). **Cliquer sur le chrono ouvre un panneau de réglages** : durée du décompte (0/5/10/15/20/30 s), **time cap** (± 1 min) et **mode de score**. Mode **FOR TIME** (For Time/RFT/Chipper/Pyramides) : le chrono **monte**, arrêt manuel ou au time cap → **temps final = score**. Mode **AMRAP** (AMRAP/EMOM/Death By/Tabata/échelles) : le chrono **descend** depuis le cap, **compteur de reps/rounds** (+1 / −) → **score**. À la fin, le **score est enregistré comme séance faite** (`/sessions/save`, statut `done`, score dans le détail) → suivi dans l'agenda/l'historique.

**Tooltips RPE** (`components/RpeScale.tsx`) : barème RPE 1-10 (Borg CR10 adaptée, aligné sur `engines/coach_chat → RPE_SCALE`). Au **survol** (web) ou à l'**appui** (natif) d'un chiffre RPE, une **fenêtre temporaire** explique le niveau (libellé, zone d'intensité, reps en réserve en force). Intégré à l'écran Séance détaillée (« difficulté ressentie »). Le Coach Chat sait aussi expliquer un RPE précis (« c'est quoi un RPE 8 ? »).

**État** : 119 tests pytest + 4 audits 100 samples PASS (49 routes API), TypeScript strict 0 erreur, export web OK. Aucune régression.

*Addendum v3.0 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.1 — Préparation multi-utilisateurs : persistance PostgreSQL durcie & vérifiée (16/06/2026)

> Complète les sections précédentes sans rien y modifier. **Étape 1/2** vers le multi-comptes (auth à suivre une fois PostgreSQL actif en prod).

**Contexte** : objectif d'ouvrir le site à plusieurs utilisateurs (amis) avec **comptes/login**, **isolation stricte des données** (un compte ne voit ni ne modifie les données d'un autre), l'utilisateur principal (propriétaire) **conservant intégralement son profil et son programme**. Choix validés : inscription **par code d'invitation**, **PostgreSQL d'abord**, auth **simple** (email + mot de passe haché, jeton signé, déconnexion).

**Constat d'architecture** : la base est **déjà multi-tenant par conception** — table `users` (email, password_hash) + `athlete_profiles.user_id`, et **toutes** les tables de données (`sessions`, `daily_metrics`, `pr_records`, `benchmark_results`, `training_plans`, `coach_decisions`, `nutrition_logs`, `garmin_tokens`) sont cloisonnées par `athlete_id`. Les repositories prennent déjà l'`athlete_id` en paramètre → l'isolation est structurelle. Le seul point « mono-utilisateur » restant : le serveur résout toujours « le premier athlète » et 23 endpoints utilisent cet id fixe (à remplacer par « l'utilisateur connecté » à l'étape auth).

**Persistance PostgreSQL durcie & PROUVÉE** (prérequis absolu : en SQLite sur Render free, la base est éphémère → les comptes seraient perdus à chaque redéploiement) :
- Vérifié contre un **vrai PostgreSQL 16** (pas seulement SQLite) : création des **11 tables**, seed idempotent (1 athlète, pas de doublon), écriture/relecture métriques + séances, et **persistance à travers un redémarrage simulé** (une séance écrite par un `Store` est relue par un nouveau `Store` sur la même base). `tests/test_postgres.py` (end-to-end) **PASS** sur PG réel.
- `/health` enrichi : expose désormais `db_backend` (`postgres`/`sqlite`) et `persistent` (bool) → permet de **vérifier d'un coup d'œil** que la prod tourne bien en PostgreSQL après bascule.
- `DEPLOY.md` : runbook **« Activer PostgreSQL sur un service déjà déployé »** (re-sync Blueprint Render *ou* base externe Neon/Supabase) + vérification via `/health` (`"persistent": true`).

**Garantie « données du propriétaire préservées »** : le seed du profil ne s'exécute **que** si aucun athlète n'existe (jamais d'écrasement d'un profil déjà saisi/édité, confirmé sur PG). À l'étape auth, l'athlète existant (profil réel déjà rempli) sera **rattaché au compte propriétaire** ; les nouveaux inscrits obtiennent un **profil vierge** (leur niveau/objectifs), sans aucune incidence sur le programme du propriétaire.

**Action requise côté utilisateur (avant l'étape auth)** : activer PostgreSQL sur Render (cf. DEPLOY.md) et confirmer `"persistent": true` sur `/health`.

**État** : 119 tests pytest (SQLite) + 4 tests PG (PostgreSQL réel) + 4 audits PASS (49 routes API), TypeScript strict 0 erreur, export web OK. Aucune régression.

*Addendum v3.1 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.2 — Coach Chat à cerveau local (réponses concrètes même API en veille) (16/06/2026)

> Complète l'addendum v3.0 sans rien y modifier.

**Problème constaté** : en ligne, le chatbot renvoyait toujours **le même message** quelle que soit la question. Cause : l'app web appelle l'API Render (`/coach/chat`) ; quand Render free est **en veille** (réveil 30-60 s) ou que l'endpoint n'est pas encore redéployé, l'appel échouait et l'écran affichait un **unique message d'erreur générique** — donnant l'impression d'un bot « bête ».

**Correctif** : ajout d'un **coach local** (`mobile/src/coach/localCoach.ts`), miroir TypeScript de `engines/coach_chat`, qui **analyse la question** (mêmes intentions/mots-clés) et compose une **réponse concrète personnalisée** avec le profil mis en cache (poids → protéines/lipides, VMA → allures, FCmax → zones, 1RM → objectifs force, `goal_date` → semaines avant 2029) et le **planning 3/2/2/3 calculé localement** (`schedule.ts`). Le `CoachChatScreen` tente d'abord l'API (réponse enrichie, données du jour) avec un **timeout de 8 s**, puis **bascule sur le coach local** en cas d'échec/latence → **toujours une réponse pertinente**, jamais un message unique, et **fonctionne hors ligne**. Barème RPE partagé avec `RpeScale` (source unique).

**État** : TypeScript strict 0 erreur, export web OK. Backend inchangé (119 pytest + 4 PG + 4 audits PASS).

*Addendum v3.2 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.3 — Score WOD pris en compte (charge + performance + suivi) (16/06/2026)

> Complète les addendums v3.0/v3.2 sans rien y modifier.

**Question** : le temps/score d'un WOD effectué est-il pris en compte pour l'analyse de performance et le suivi ? **Constat** : la **charge** (stress units → ACWR/fatigue/fitness) comptait déjà (séance `done`, durée dérivée du temps), mais le **score lui-même** n'était ni affiché dans le suivi ni intégré à la dimension « performance » de l'analyse (qui utilisait la *readiness* comme proxy).

**Corrections** :
- **Chrono** (`WodTimer`) : le résultat inclut désormais le **time cap** (`cap_sec`) pour permettre la normalisation de la performance.
- **Backend** : helpers `_wod_score` (extrait type/valeur/label du détail) et `_wod_performance` (score 0-100 : For Time = d'autant meilleur qu'on finit sous le cap, capé → 45 ; AMRAP = reps relatives au meilleur score connu). `/analytics/snapshot` calcule désormais `performance_scores` **à partir des WOD chronométrés** (du plus ancien au plus récent, repli readiness si < 3 WOD scorés) → la perf WOD alimente vraiment **fitness + performance + tendance**. Nouveaux champs exposés : `performance`, `performance_source` (`wod`/`readiness_proxy`), `wods_scored`. Le **score** est surfacé dans `/sessions/recent` (champ `score`) et le **label** dans `/agenda/week` (`score_label`).
- **App** : l'Agenda (vue SUIVI) affiche le score (🏁 temps / 🔁 reps) sur les WOD faits ; l'onglet OBJECTIFS gagne une carte **« DERNIERS WODS — PERFORMANCE »** (date · nom · score) alimentée par l'historique.

**État** : 123 tests pytest (SQLite) + 4 tests PG + 4 audits PASS (49 routes API), TypeScript strict 0 erreur, export web OK. Aucune régression.

*Addendum v3.3 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.4 — Bips chrono (10 dernières s) + séance du jour cohérente partout (16/06/2026)

> Complète les addendums v3.0–v3.3 sans rien y modifier.

**Bips chrono** (`WodTimer`) : en plus du décompte de départ (3-2-1 + GO), des **bips sur les 10 dernières secondes** — d'un AMRAP comme avant la fin du time cap d'un For Time (les 3 derniers plus marqués, bip de fin).

**Cohérence des séances (correctif majeur)** : la séance d'un même jour différait entre l'écran **JOUR**, l'onglet **SÉANCES** et l'**AGENDA**, car trois chemins de génération indépendants coexistaient (décision adaptative / générateurs libres / plan hebdo). Désormais **une source unique** : le plan hebdomadaire déterministe (mêmes templates 3/2/2/3 + mêmes seeds par semaine/jour).
- **Backend** : `weekly_plan.build_day(date)` + endpoint `GET /plan/day?date=` (mêmes seeds que `/plan/weekly` → séance identique pour une date). Test de cohérence `/plan/day` ↔ `/plan/weekly` (titres + détails identiques) et déterminisme.
- **App** : nouveau composant partagé `PlannedSessions` (rendu unique des séances d'un jour) utilisé par l'**Agenda** (plan détaillé), l'écran **JOUR** (séance(s) du jour via `/plan/day`, avec « marquer fait » + RPE intégré) et l'onglet **SÉANCES** (carte « SÉANCE DU JOUR · selon ton plan » par discipline). Les générateurs deviennent une section « EXPLORER / GÉNÉRER UNE VARIANTE » clairement distincte. L'écran JOUR conserve le **conseil adaptatif** (readiness → intensité/prudence) en bandeau, mais le **contenu de la séance est le plan** → identique partout, sur toutes les semaines. Écran `SessionDetailScreen` (format adaptatif divergent) retiré ; sa complétion RPE est reprise dans `PlannedSessions`.

**État** : 126 tests pytest (SQLite) + 4 tests PG + 4 audits PASS (50 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.4 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.5 — Mode standby / vacances (par athlète) (16/06/2026)

> Complète les sections précédentes sans rien y modifier. Répond au « mode standby » du prompt initial.

Quand l'athlète s'absente, deux modes adaptent l'entraînement, **configurés dans Profil** via une fenêtre de dates (« départ dans N jours » + durée), **stockés par athlète** (`standby_state`, une ligne/athlète, isolation totale — aucun impact sur les autres comptes) :

- **PAUSE** (pas de salle / pas le temps) : le plan est **gelé** pendant l'absence ; au retour, **une semaine de reprise progressive (deload)** — volume/intensité réduits, anti-lombaire — puis le plan **reprend exactement là où il s'était arrêté** : la progression est **décalée** (cumulée dans `plan_shift_weeks`), donc **aucun cycle 5/3/1 n'est perdu**. Pliage paresseux : une fois la pause + sa semaine de reprise passées, le décalage est figé.
- **VACANCES** (plus de temps) : **bloc intensif salle complète**, **réglable à l'activation** (durée 5-7 j via la fenêtre, **1 ou 2 séances/jour**), rotation 6 jours orientée RAID (force push/pull/legs + course seuil/VMA/Z2 + WOD), cohérent et **anti-lombaire**. Le plan normal reprend à la fin (sans décalage : tu t'es entraîné).

**Implémentation** :
- Backend : table `standby_state` + `StandbyRepository` ; moteur `engines/standby/` (classification jour, pliage, générateurs reprise/vacances réutilisant run/force/WOD) ; refonte `weekly_plan._day_payload` pour décaler **seulement la progression** (cycle/seeds) en gardant la **structure calendaire réelle** (jours travaillés/OFF, type de semaine). Endpoints `GET/POST/DELETE /standby` ; `/plan/day` et `/plan/weekly` tiennent compte du standby → **JOUR, SÉANCES et AGENDA restent cohérents**. Vérifié sur **PostgreSQL réel** (table créée, upsert sans doublon).
- App : carte **« MODE VACANCES / STANDBY »** dans Profil (choix mode, fenêtre, séances/jour, activation/annulation) ; bandeau standby (⏸ standby / ↩ reprise / 🏝 vacances) affiché dans l'écran Jour, l'onglet Séances et l'Agenda via le composant partagé `PlannedSessions`. Invalidation des caches de plan à l'activation.

**État** : 131 tests pytest (SQLite) + 4 tests PG + 4 audits PASS (53 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.5 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.6 — Préparation persistance PostgreSQL : runbook durable + log de démarrage (16/06/2026)

> Complète les addendums v3.1/v3.5. Étape côté code pour fiabiliser le passage en production persistante (l'activation reste une action dans le dashboard Render, non automatisable depuis le dépôt).

- **DEPLOY.md** : runbook « Activer PostgreSQL » restructuré. Avertissement clé : la base **PostgreSQL *free* de Render est supprimée après ~30 jours** → pour un **multi-utilisateurs durable**, l'option recommandée est **Neon** (gratuit, sans expiration), avec procédure pas-à-pas (`DATABASE_URL` dans Render → Environment). Vérification via `/health` (`"persistent": true`).
- **Log de démarrage** : l'API logue désormais son backced DB (`postgres (persistant)` / `sqlite (EPHEMERE)`) → visible dans les logs Render pour confirmer la persistance sans appel réseau.
- Rappel : le schéma complet (toutes les tables, dont `users` et `standby_state`) se crée automatiquement au démarrage sur PostgreSQL — vérifié sur un PostgreSQL 16 réel (création + données conservées après redémarrage simulé).

**État** : 131 tests pytest + 4 tests PG + 4 audits PASS (53 routes), TypeScript strict 0 erreur, export web OK.

*Addendum v3.6 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.7 — Authentification multi-utilisateurs (construit, NON déployé) (16/06/2026)

> ⚠️ Code prêt sur la branche de travail mais **pas encore déployé** (choix utilisateur : valider avant d'exiger une connexion sur le site). PostgreSQL confirmé persistant au préalable (`/health` → `"persistent": true`).

Comptes **email + mot de passe**, **par athlète**, avec **isolation stricte** des données. Choix retenus : inscription **par code d'invitation**, **1er inscrit = propriétaire** (récupère le profil existant, données intactes), auth **simple**.

**Backend** (sans dépendance externe) :
- `api/auth.py` : mots de passe **PBKDF2-HMAC-SHA256** (sel par utilisateur), **jetons signés HMAC** (payload `{uid, exp}`, TTL 30 j). Secret serveur **généré et stocké en base** (`app_meta`) → stable entre redéploiements, sans variable d'env.
- Endpoints `POST /auth/register` (1er = propriétaire via `claim_owner` sur le profil primaire ; sinon `INVITE_CODE` requis), `POST /auth/login`, `GET /auth/me`.
- Résolution de l'utilisateur courant par **middleware ASGI pur** (contextvar fiable jusqu'au handler sync) → `_aid()` remplace l'athlète fixe dans tous les endpoints data. **Repli sur le propriétaire si aucun jeton** (compat mono-utilisateur, non-bloquant) ; passe en **401** si `AUTH_REQUIRED` est défini (enforcement serveur). Générateurs (`/generate/*`, infos nutrition) restent publics.
- Tables : `app_meta` ajoutée (id + key unique). Aucune modification de colonnes sur tables existantes → migration auto au démarrage. **Vérifié sur PostgreSQL 16 réel** : inscription propriétaire (données intactes), ami par code, **isolation** (métriques/séances cloisonnées), et **login conservé après redémarrage** (secret + comptes persistés). Bug attrapé sur PG (RETURNING id sur table sans `id`) → corrigé.

**App** : écran **Connexion / Inscription** (`AuthScreen`) ; le client stocke le jeton (AsyncStorage) et l'envoie sur chaque requête ; **401 → retour login**. `App.tsx` restaure la session au lancement (`/auth/me`) et gate l'accès. Carte **COMPTE** dans Profil (email, badge propriétaire, déconnexion).

**Pour activer (quand prêt)** : (1) déployer la branche, (2) s'inscrire en 1er = propriétaire (profil récupéré), (3) définir `INVITE_CODE` dans Render pour ouvrir l'inscription aux amis, (4) optionnel : `AUTH_REQUIRED=1` pour l'enforcement serveur. Détails à ajouter dans DEPLOY.md à l'activation.

**État** : 139 tests pytest (SQLite) + 4 tests PG + auth vérifiée sur PG réel + 4 audits PASS (56 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.7 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.8 — Rythme de travail par utilisateur + onboarding (construit, NON déployé) (16/06/2026)

> Suite de l'auth (même branche, non déployée). Chaque compte a son propre rythme de travail ; le plan s'adapte.

**Rythme par athlète** (stocké dans `athlete_profiles.work_schedule`, JSON, par compte → isolation totale) :
- **3/2/2/3 (police)** avec **ancre propre** → gère les collègues en **cycle opposé** (ancre décalée d'une semaine). Le propriétaire garde son ancre.
- **Hebdomadaire** : l'athlète choisit ses **jours d'entraînement** ; les autres = repos. Rotation équilibrée force/course/WOD (anti-lombaire) répartie sur ces jours, variée par semaine.

**Backend** : nouveau `engines/schedule/user_schedule.py` (config-driven : `normalize`, `day_schedule`, `week_schedule`, `week_template`). `police_schedule` paramétré par **ancre** (rétro-compatible). `weekly_plan` (build_day/build_weekly), `standby` (planned_day/reboot), et `coach_api` (schedule_day/week, session_today, plan) prennent désormais une **config**. L'API résout la config de l'utilisateur courant (`_schedule_config()`) et la passe partout (`/plan/day`, `/plan/weekly`, `/agenda/week`, `/coach/session`, `/schedule/*`). `PATCH /profile` accepte `work_schedule` (normalisé serveur). Garde-fou budget hebdo pour le type weekly. Tests : plan hebdo (séances seulement les jours choisis), phase police opposée (type de semaine inversé), isolation par compte.

**App** : `schedule.ts` rendu config-aware (mirror) → `WeekStrip` et l'écran Jour affichent le rythme de chacun (3/2/2/3 grande/petite, ou hebdo entraînement/repos). Nouvel **OnboardingScreen** (après 1ère connexion, si pas de rythme) : niveau (VMA/FCmax), objectif (but + échéance) et rythme (3/2/2/3 « grande/petite cette semaine » ou hebdo « jours choisis ») → `PATCH /profile`. Gate d'onboarding dans `App.tsx`. Modifiable ensuite.

> Personnalisation des **charges de force** (TM 5/3/1 selon le 1RM de chacun) = prochaine étape ; aujourd'hui les allures course se personnalisent déjà via VMA/FCmax du compte.

**État** : 141 tests pytest (SQLite) + auth/schéma vérifiés sur PostgreSQL réel + 4 audits PASS (56 routes), TypeScript strict 0 erreur, export web OK. **Non déployé.**

*Addendum v3.8 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.9 — Personnalisation (1RM par utilisateur), saisie clavier, PDC, suppression de séance, code d'invitation in-app (16/06/2026)

> Retours utilisateurs (amis). Déployé.

- **1RM par utilisateur → charges 5/3/1 personnalisées** (fini le DC 90 kg imposé). Le moteur force accepte des `maxes` (1RM par mouvement) ; chaque athlète stocke ses 1RM (benchmarks `{lift}_1rm`), TM = 90 % arrondi 2,5 kg. Threadé dans `weekly_plan`, `standby`, `coach_api`, et l'API (`_strength_maxes()` par athlète) → `/generate/strength`, `/strength/cycle`, `/strength/progression`, `/plan/day`, `/plan/weekly` utilisent les 1RM de chacun. App : composant **`LiftMaxes`** dans Profil (DC/Squat/OHP/Row éditables, recalcul du plan à l'enregistrement). Test : 1RM 120 → TM 107,5 (≠ défaut 90).
- **Saisie clavier** : composant **`NumberField`** (boutons +/− ET appui sur la valeur → clavier numérique). Remplace les steppers clés : poids (Profil), VMA/FC/échéance (Onboarding), durée WOD, suivi benchmarks.
- **Séances PDC (poids du corps)** : `generate_wod(..., bodyweight=True)` filtre les mouvements gym sans charge (ni machine, ni haltéro) ; toggle **« PDC »** dans le générateur WOD. Test dédié (aucune charge `@kg`).
- **Supprimer une séance « faite »** (annulation mauvaise manip) : `DELETE /sessions/{id}` (isolé par athlète) ; bouton ✕ dans l'Agenda (vue Suivi). Test d'isolation (un autre compte ne peut pas supprimer).
- **Code d'invitation géré dans l'app** (sans Render) : stocké en base (`app_meta`, privé), réglé par le **propriétaire** (`GET/POST /auth/invite-code`) ; l'inscription accepte le code app_meta **ou** la variable d'env. App : carte **`InviteCodeCard`** dans Profil (propriétaire). Test : owner définit le code, l'ami s'inscrit, un non-propriétaire ne peut pas le changer.

**État** : 146 tests pytest (SQLite) + auth/schéma/PG vérifiés + 4 audits PASS (59 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.9 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.10 — Séances libres (hors plan) + coach chatbot LLM (16/06/2026)

> Retours utilisateurs. Déployé.

- **Séances LIBRES (hors plan)** : vélo, boxe, JJB, natation, rando, mobilité, autre. Endpoint `POST /sessions/manual` (activité libre + durée + RPE + métriques optionnelles : distance, FC moy/max, dénivelé, calories, notes) → enregistrée **faite**, SU calculées → **comptée dans le suivi** (charge/ACWR, agenda, historique). App : **segment « AUTRE »** dans l'onglet SÉANCES (`ManualSessionForm`), saisie clavier, sélection du jour, métriques optionnelles. Libellés/glyphes ajoutés (vélo/combat/rando/mobilité/libre). Tests : la séance compte dans la charge et apparaît dans l'agenda.
- **Coach chatbot LLM** : `/coach/chat` route désormais vers l'**API Claude** si `ANTHROPIC_API_KEY` est défini (sinon repli sur le coach déterministe, et repli local côté app). `engines/coach_chat/llm.py` (urllib, sans dépendance) : prompt système « coach personnel expert » + **contexte athlète** (profil, blessure, jour) + **historique de conversation** → répond à **toute** question (sport, nutrition, compléments, sommeil, récup, blessure…). Modèle configurable (`COACH_MODEL`, défaut Haiku). App : le chat envoie l'historique récent ; message d'accueil élargi. Test : repli déterministe sans clé.

**Activation du coach intelligent (côté utilisateur)** : Render → service → Environment → `ANTHROPIC_API_KEY` = clé Anthropic (facturation à l'usage, ~centimes ; modèle Haiku économique). Sans clé, le coach reste déterministe.

**État** : 149 tests pytest (SQLite) + auth/schéma/PG vérifiés + 4 audits PASS (60 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.10 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.11 — Trap-barre, full body, WOD team, ratios auto, montée de corde (16/06/2026)

> Retours utilisateurs. Déployé.

- **Soulevé de terre trap-barre** ajouté pour tout le monde : accessoire jour LEGS (en tête) + présent en full body (plus sûr pour le dos que le DL classique).
- **Style FULL BODY** (par utilisateur, choix à l'onboarding et dans Profil) : chaque séance force devient corps entier (**squat + DC + rowing** en principaux + accessoires courts dont trap-barre), **1h-1h15 max**, toujours **selon le rythme 3/2/2/3 ou hebdo et le mode standby**. `training_style` ('split'|'fullbody') dans la config rythme ; `generate_strength_531('fullbody')` renvoie `main_lifts` (3 lifts) ; `weekly_plan` remappe les séances force en full body. App : rendu multi-lifts (`StrengthDetail`), bascule Split/Full body dans Profil + onboarding.
- **WOD TEAM** : `generate_wod(team_size=1..4)` → en-tête équipe (« I go you go », relais, répartition…), score « cumul équipe ». Sélecteur SOLO/×2/×3/×4 dans le générateur WOD.
- **Ratios DC/Squat auto-remplis** depuis le **1RM réel saisi** et le **poids** de chacun : `current_maxes` injecte `bench_ratio`/`squat_ratio` = `{lift}_1rm` (le rapport force divise par le poids de corps) → plus de valeurs imposées.
- **Montée de corde max** éditable : ajoutée au suivi chiffré (OBJECTIFS) — `rope_climb_5m`, saisie clavier.

**État** : 153 tests pytest + auth/schéma/PG vérifiés + 4 audits PASS (60 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.11 · 16/06/2026 · Claude Code.*

-----

### Addendum v3.12 — Redémarrage du programme + progression par J0 utilisateur (16/06/2026)

> Déployé.

- **Progression 5/3/1 relative au J0 de chaque athlète** (et non plus à l'ancre globale 2026-06-15) : `user_schedule.plan_start(config)` = ancre police (lundi de grande semaine = J0) ou `start_monday` (weekly). Chaque utilisateur démarre au **cycle 0** à sa date de début → corrige la progression des nouveaux comptes (ils ne démarrent plus « en plein cycle »). Rétro-compatible (propriétaire : ancre = START → inchangé).
- **Redémarrer le programme** (Profil) : bouton qui re-fixe l'ancre/`start_monday` au **lundi prochain** → cycle 5/3/1 remis à **zéro**, **grande semaine**, à partir de ce lundi, sans toucher à l'historique. Confirmation en 2 temps ; invalide le cache plan. Test : ré-ancrer → `week_index` 0 (grande) le J0, 2 deux semaines plus tard.

**État** : 154 tests pytest + 4 audits PASS (60 routes API), TypeScript strict 0 erreur, export web OK.

*Addendum v3.12 · 16/06/2026 · Claude Code.*