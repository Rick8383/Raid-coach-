"""Persistance pour l'API (B13 → B12).

Mode mono-athlète : l'app est utilisée par un seul athlète aujourd'hui. Au
démarrage, on garantit un user + profil athlète par défaut, pré-rempli avec
les données réelles (cf. PROJECT_MASTER) et les maxes actuels (benchmarks).
DB : fichier SQLite par défaut (RAID_COACH_DB), ":memory:" en tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from db.database import Database
from db.repositories.repositories import (AthleteRepository,
                                          BenchmarkRepository,
                                          MetricsRepository,
                                          SessionRepository)

DEFAULT_DB_PATH = os.environ.get("RAID_COACH_DB", "data/raid_coach.db")

# Profil réel (verrouillé 11/06/2026, cf. PROJECT_MASTER §15)
_DEFAULT_PROFILE = {
    "birth_date": "1995-07-30",
    "height_cm": 172.0,
    "weight_kg": 75.0,
    "target_weight_kg": 79.0,
    "body_fat_pct": 15.0,
    "vma_kmh": 13.6,
    "fc_max": 186,
    "main_goal": "Sélection RAID 2029",
    "goal_date": "2029-03-01",
    "injuries": [{"zone": "L5-S1", "type": "sciatique", "note": "gêne > douleur, gérer charge axiale"}],
    "work_schedule": {"pattern": "3/2/2/3", "anchor_big_week_monday": "2026-06-15"},
}

# Maxes actuels → benchmark_results (mêmes clés que /raid/strength-report attend)
_DEFAULT_BENCHMARKS = [
    ("pullups_max", 16, "reps"), ("pushups_max", 60, "reps"),
    ("dips_max", 40, "reps"), ("leg_raises_max", 18, "reps"),
    ("rope_climb_5m", 1, "reps"), ("cooper_m", 2850, "m"),
    ("bench_ratio", 95, "kg"), ("squat_ratio", 110, "kg"),
]

# Clés assemblées dans le champ `current` du profil (pour /raid/strength-report)
CURRENT_KEYS = [b[0] for b in _DEFAULT_BENCHMARKS]


class Store:
    """Database + repositories utilisés par les endpoints de persistance."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = Database(db_path)
        self.athletes = AthleteRepository(self.db)
        self.metrics = MetricsRepository(self.db)
        self.sessions = SessionRepository(self.db)
        self.benchmarks = BenchmarkRepository(self.db)
        self.athlete_id = self._ensure_default_athlete()

    def _ensure_default_athlete(self) -> int:
        rows = self.db.query("SELECT id FROM athlete_profiles ORDER BY id LIMIT 1")
        if rows:
            return rows[0]["id"]
        user_id = self.athletes.create_user("athlete@raid-coach.local", "!local-single-user")
        athlete_id = self.athletes.create_profile(user_id, "Athlète RAID", **_DEFAULT_PROFILE)
        for bid, value, unit in _DEFAULT_BENCHMARKS:
            self.benchmarks.record(athlete_id, bid, float(value), unit, "2026-06-11")
        return athlete_id

    def current_maxes(self) -> dict:
        """Dernière valeur connue pour chaque benchmark suivi (max actuels)."""
        out: dict[str, float] = {}
        for key in CURRENT_KEYS:
            prog = self.benchmarks.progression(self.athlete_id, key)
            if prog:
                out[key] = prog[-1]["result_value"]
        return out

    def profile_payload(self) -> dict:
        """Profil complet pour l'app : champs athlète + maxes actuels assemblés."""
        prof = self.athletes.get_profile(self.athlete_id) or {}
        for jf in ("injuries", "work_schedule"):
            if isinstance(prof.get(jf), str):
                try:
                    prof[jf] = json.loads(prof[jf])
                except (ValueError, TypeError):
                    pass
        prof["current"] = self.current_maxes()
        return prof
