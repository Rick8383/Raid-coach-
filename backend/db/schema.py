"""BUILD 13 — Database schema.

Two layers:
1. SCHEMA_SQL: canonical PostgreSQL DDL (source of truth).
2. SQLAlchemy models (db/orm_models.py) mirroring this DDL — used in production.

The DDL is also executable against SQLite for local/sandbox testing
(types degrade gracefully)."""
from __future__ import annotations

SCHEMA_VERSION = "13.0"

SCHEMA_SQL = """
-- ============ CORE ============
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS athlete_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    birth_date TEXT,
    height_cm REAL,
    weight_kg REAL,
    target_weight_kg REAL,
    fc_max INTEGER,
    fc_rest INTEGER,
    vma_kmh REAL,
    body_fat_pct REAL,
    injuries TEXT,                -- JSON: [{"zone":"L5-S1","type":"sciatique",...}]
    work_schedule TEXT,           -- JSON: police 3/2/2/3 pattern
    main_goal TEXT,               -- "RAID selection 2029"
    goal_date TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============ TRAINING ============
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    discipline TEXT NOT NULL,     -- run|crossfit|strength|swim|recovery
    session_date TEXT NOT NULL,
    duration_min INTEGER,
    intensity_rpe REAL,
    stress_units REAL,
    family_id TEXT,
    template_id TEXT,
    detail_json TEXT,             -- full generated session payload
    status TEXT NOT NULL DEFAULT 'planned',  -- planned|done|skipped|modified
    feedback_json TEXT,           -- post-session athlete feedback
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sessions_athlete_date ON sessions(athlete_id, session_date);

CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    metric_date TEXT NOT NULL,
    readiness REAL,
    fatigue REAL,
    sleep_quality REAL,
    sleep_hours REAL,
    hrv REAL,
    resting_hr INTEGER,
    weight_kg REAL,
    pain_flag INTEGER DEFAULT 0,
    sciatic_flare INTEGER DEFAULT 0,
    notes TEXT,
    UNIQUE(athlete_id, metric_date)
);

-- ============ PROGRESS ============
CREATE TABLE IF NOT EXISTS pr_records (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    movement_id TEXT NOT NULL,
    weight_kg REAL,
    reps INTEGER NOT NULL,
    e1rm REAL,
    record_date TEXT NOT NULL,
    bodyweight_kg REAL
);
CREATE INDEX IF NOT EXISTS idx_pr_athlete_movement ON pr_records(athlete_id, movement_id);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    benchmark_id TEXT NOT NULL,   -- ex: "wod_selection_pdc_2026", "cooper", "pullups_max"
    result_value REAL NOT NULL,   -- rounds+reps, meters, reps, seconds...
    result_unit TEXT NOT NULL,
    result_detail TEXT,           -- JSON breakdown
    test_date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bench_athlete ON benchmark_results(athlete_id, benchmark_id);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    snapshot_date TEXT NOT NULL,
    fitness REAL, fatigue REAL, readiness REAL,
    risk REAL, performance REAL,
    acwr REAL,
    raid_readiness_pass REAL,
    raid_readiness_elite REAL,
    UNIQUE(athlete_id, snapshot_date)
);

-- ============ PLANS ============
CREATE TABLE IF NOT EXISTS training_plans (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    goal_type TEXT NOT NULL,
    goal_name TEXT NOT NULL,
    duration_weeks INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- active|completed|abandoned
    plan_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coach_decisions (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    decision_date TEXT NOT NULL,
    decision_type TEXT NOT NULL,  -- daily|budget|arbitration
    context_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_decisions_athlete ON coach_decisions(athlete_id, decision_date);

-- ============ NUTRITION ============
CREATE TABLE IF NOT EXISTS nutrition_logs (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    log_date TEXT NOT NULL,
    calories INTEGER, protein_g INTEGER, carbs_g INTEGER, fat_g INTEGER,
    water_l REAL,
    target_json TEXT,             -- the MacroTarget that was prescribed
    adherence_pct REAL,
    UNIQUE(athlete_id, log_date)
);

-- ============ INTÉGRATIONS (OAuth montre) ============
CREATE TABLE IF NOT EXISTS garmin_tokens (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    request_token TEXT,
    request_token_secret TEXT,
    access_token TEXT,
    access_token_secret TEXT,
    connected_at TEXT,
    UNIQUE(athlete_id)
);

-- ============ MODE STANDBY / VACANCES ============
-- Une ligne par athlète (isolation totale entre utilisateurs). `mode` :
--   NULL/''  = pas de standby actif
--   'pause'  = absence sans entraînement → plan gelé, décalé au retour + deload
--   'vacation' = bloc d'entraînement intensif sur la fenêtre
-- plan_shift_weeks = décalage cumulé du plan (semaines), dû aux pauses passées.
CREATE TABLE IF NOT EXISTS standby_state (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athlete_profiles(id),
    mode TEXT,
    start_date TEXT,
    end_date TEXT,
    params_json TEXT,
    plan_shift_weeks INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(athlete_id)
);
-- ============ MÉTA APPLICATION (secret d'auth, propriétaire…) ============
CREATE TABLE IF NOT EXISTS app_meta (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT
);
"""

TABLES = ["users", "athlete_profiles", "sessions", "daily_metrics",
          "pr_records", "benchmark_results", "analytics_snapshots",
          "training_plans", "coach_decisions", "nutrition_logs",
          "garmin_tokens", "standby_state", "app_meta"]
