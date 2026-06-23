from __future__ import annotations

import json
from ..database import Database

# Allowlists : les noms de colonnes sont interpolés dans le SQL (les valeurs
# restent paramétrées) — tout champ inconnu est rejeté avant interpolation.
_PROFILE_COLUMNS = frozenset({
    "birth_date", "height_cm", "weight_kg", "target_weight_kg", "fc_max",
    "fc_rest", "vma_kmh", "body_fat_pct", "injuries", "work_schedule",
    "main_goal", "goal_date"})
_METRIC_COLUMNS = frozenset({
    "readiness", "fatigue", "sleep_quality", "sleep_hours", "hrv",
    "resting_hr", "weight_kg", "pain_flag", "sciatic_flare", "notes"})


def _check_columns(fields: dict, allowed: frozenset, table: str) -> None:
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"unknown {table} column(s): {sorted(unknown)}")


class AthleteRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_user(self, email: str, password_hash: str) -> int:
        cur = self.db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash))
        return cur.lastrowid

    def create_profile(self, user_id: int, name: str, **fields) -> int:
        _check_columns(fields, _PROFILE_COLUMNS, "athlete_profiles")
        cols = ["user_id", "name"] + list(fields.keys())
        vals = [user_id, name] + [json.dumps(v) if isinstance(v, (dict, list)) else v
                                  for v in fields.values()]
        sql = f"INSERT INTO athlete_profiles ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
        return self.db.execute(sql, tuple(vals)).lastrowid

    def get_profile(self, athlete_id: int) -> dict | None:
        rows = self.db.query("SELECT * FROM athlete_profiles WHERE id = ?", (athlete_id,))
        return rows[0] if rows else None

    def update_profile(self, athlete_id: int, **fields) -> None:
        if not fields:
            return
        _check_columns(fields, _PROFILE_COLUMNS, "athlete_profiles")
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        self.db.execute(
            f"UPDATE athlete_profiles SET {sets}, updated_at = datetime('now') WHERE id = ?",
            tuple(vals) + (athlete_id,))

    # ---- Authentification multi-utilisateurs ----
    def find_user_by_email(self, email: str) -> dict | None:
        rows = self.db.query("SELECT * FROM users WHERE email = ?", (email,))
        return rows[0] if rows else None

    def get_user(self, user_id: int) -> dict | None:
        rows = self.db.query("SELECT * FROM users WHERE id = ?", (user_id,))
        return rows[0] if rows else None

    def set_user_credentials(self, user_id: int, email: str, password_hash: str) -> None:
        self.db.execute("UPDATE users SET email = ?, password_hash = ? WHERE id = ?",
                        (email, password_hash, user_id))

    def athlete_id_for_user(self, user_id: int) -> int | None:
        rows = self.db.query(
            "SELECT id FROM athlete_profiles WHERE user_id = ? ORDER BY id LIMIT 1",
            (user_id,))
        return rows[0]["id"] if rows else None

    def user_id_for_athlete(self, athlete_id: int) -> int | None:
        rows = self.db.query(
            "SELECT user_id FROM athlete_profiles WHERE id = ?", (athlete_id,))
        return rows[0]["user_id"] if rows else None


class AppMetaRepository:
    """Clé/valeur applicatif (secret d'auth, identifiant du propriétaire…)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, key: str) -> str | None:
        rows = self.db.query("SELECT value FROM app_meta WHERE key = ?", (key,))
        return rows[0]["value"] if rows else None

    def set(self, key: str, value: str) -> None:
        self.db.execute(
            """INSERT INTO app_meta (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value))


class SessionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, athlete_id: int, discipline: str, session_date: str,
               duration_min: int, intensity_rpe: float, stress_units: float,
               detail: dict, status: str = "planned",
               family_id: str | None = None, template_id: str | None = None) -> int:
        return self.db.execute(
            """INSERT INTO sessions (athlete_id, discipline, session_date,
               duration_min, intensity_rpe, stress_units, family_id,
               template_id, detail_json, status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (athlete_id, discipline, session_date, duration_min, intensity_rpe,
             stress_units, family_id, template_id, json.dumps(detail), status)
        ).lastrowid

    def complete(self, session_id: int, feedback: dict | None = None) -> None:
        self.db.execute(
            "UPDATE sessions SET status = 'done', feedback_json = ? WHERE id = ?",
            (json.dumps(feedback or {}), session_id))

    def last_n(self, athlete_id: int, n: int = 20) -> list[dict]:
        return self.db.query(
            """SELECT * FROM sessions WHERE athlete_id = ?
               ORDER BY session_date DESC, id DESC LIMIT ?""", (athlete_id, n))

    def stress_units_between(self, athlete_id: int, date_from: str, date_to: str) -> float:
        rows = self.db.query(
            """SELECT COALESCE(SUM(stress_units), 0) AS su FROM sessions
               WHERE athlete_id = ? AND status = 'done'
               AND session_date BETWEEN ? AND ?""",
            (athlete_id, date_from, date_to))
        return float(rows[0]["su"])

    def recent_family_ids(self, athlete_id: int, n: int = 20) -> list[str]:
        rows = self.db.query(
            """SELECT family_id FROM sessions WHERE athlete_id = ?
               AND family_id IS NOT NULL ORDER BY session_date DESC LIMIT ?""",
            (athlete_id, n))
        return [r["family_id"] for r in rows]


class MetricsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, athlete_id: int, metric_date: str, **metrics) -> None:
        _check_columns(metrics, _METRIC_COLUMNS, "daily_metrics")
        cols = ["athlete_id", "metric_date"] + list(metrics.keys())
        vals = [athlete_id, metric_date] + list(metrics.values())
        updates = ", ".join(f"{k} = excluded.{k}" for k in metrics)
        self.db.execute(
            f"""INSERT INTO daily_metrics ({','.join(cols)})
                VALUES ({','.join('?' * len(cols))})
                ON CONFLICT(athlete_id, metric_date) DO UPDATE SET {updates}""",
            tuple(vals))

    def latest(self, athlete_id: int) -> dict | None:
        rows = self.db.query(
            """SELECT * FROM daily_metrics WHERE athlete_id = ?
               ORDER BY metric_date DESC LIMIT 1""", (athlete_id,))
        return rows[0] if rows else None


class PRRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, athlete_id: int, movement_id: str, weight_kg: float,
               reps: int, e1rm: float, record_date: str,
               bodyweight_kg: float | None = None) -> int:
        return self.db.execute(
            """INSERT INTO pr_records (athlete_id, movement_id, weight_kg,
               reps, e1rm, record_date, bodyweight_kg) VALUES (?,?,?,?,?,?,?)""",
            (athlete_id, movement_id, weight_kg, reps, e1rm, record_date,
             bodyweight_kg)).lastrowid

    def history(self, athlete_id: int, movement_id: str) -> list[dict]:
        return self.db.query(
            """SELECT * FROM pr_records WHERE athlete_id = ? AND movement_id = ?
               ORDER BY record_date""", (athlete_id, movement_id))

    def best_e1rm(self, athlete_id: int, movement_id: str) -> float | None:
        rows = self.db.query(
            """SELECT MAX(e1rm) AS best FROM pr_records
               WHERE athlete_id = ? AND movement_id = ?""",
            (athlete_id, movement_id))
        return rows[0]["best"]


class BenchmarkRepository:
    """Selection WODs and standard tests tracked over time."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, athlete_id: int, benchmark_id: str, result_value: float,
               result_unit: str, test_date: str, detail: dict | None = None) -> int:
        return self.db.execute(
            """INSERT INTO benchmark_results (athlete_id, benchmark_id,
               result_value, result_unit, result_detail, test_date)
               VALUES (?,?,?,?,?,?)""",
            (athlete_id, benchmark_id, result_value, result_unit,
             json.dumps(detail or {}), test_date)).lastrowid

    def progression(self, athlete_id: int, benchmark_id: str) -> list[dict]:
        return self.db.query(
            """SELECT test_date, result_value, result_unit FROM benchmark_results
               WHERE athlete_id = ? AND benchmark_id = ? ORDER BY test_date""",
            (athlete_id, benchmark_id))


class PlanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, athlete_id: int, goal_type: str, goal_name: str,
             duration_weeks: int, start_date: str, plan: dict) -> int:
        # Only one active plan at a time
        self.db.execute(
            "UPDATE training_plans SET status = 'abandoned' WHERE athlete_id = ? AND status = 'active'",
            (athlete_id,))
        return self.db.execute(
            """INSERT INTO training_plans (athlete_id, goal_type, goal_name,
               duration_weeks, start_date, plan_json) VALUES (?,?,?,?,?,?)""",
            (athlete_id, goal_type, goal_name, duration_weeks, start_date,
             json.dumps(plan))).lastrowid

    def active(self, athlete_id: int) -> dict | None:
        rows = self.db.query(
            "SELECT * FROM training_plans WHERE athlete_id = ? AND status = 'active'",
            (athlete_id,))
        return rows[0] if rows else None


class StandbyRepository:
    """Mode standby / vacances — une ligne par athlète (isolation totale)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, athlete_id: int) -> dict | None:
        rows = self.db.query(
            "SELECT * FROM standby_state WHERE athlete_id = ?", (athlete_id,))
        return rows[0] if rows else None

    def set_window(self, athlete_id: int, mode: str | None, start_date: str | None,
                   end_date: str | None, params: dict | None,
                   plan_shift_weeks: int) -> None:
        self.db.execute(
            """INSERT INTO standby_state
               (athlete_id, mode, start_date, end_date, params_json, plan_shift_weeks)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(athlete_id) DO UPDATE SET
                 mode = excluded.mode, start_date = excluded.start_date,
                 end_date = excluded.end_date, params_json = excluded.params_json,
                 plan_shift_weeks = excluded.plan_shift_weeks,
                 updated_at = datetime('now')""",
            (athlete_id, mode, start_date, end_date,
             json.dumps(params or {}), plan_shift_weeks))


class DecisionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def log(self, athlete_id: int, decision_date: str, decision_type: str,
            context: dict, output: dict) -> int:
        return self.db.execute(
            """INSERT INTO coach_decisions (athlete_id, decision_date,
               decision_type, context_json, output_json) VALUES (?,?,?,?,?)""",
            (athlete_id, decision_date, decision_type,
             json.dumps(context), json.dumps(output))).lastrowid

    def for_date(self, athlete_id: int, decision_date: str) -> list[dict]:
        return self.db.query(
            """SELECT * FROM coach_decisions WHERE athlete_id = ?
               AND decision_date = ?""", (athlete_id, decision_date))
