"""Persistence wiring for the API (B13 → B12).

Single-athlete mode: the app is used by one athlete today. On startup we
ensure a default user + athlete profile (id stored in DEFAULT_ATHLETE_ID).
DB backend: SQLite file by default (RAID_COACH_DB env var), ":memory:" in tests.
"""
from __future__ import annotations

import os
from pathlib import Path

from db.database import Database
from db.repositories.repositories import (BenchmarkRepository,
                                          MetricsRepository,
                                          SessionRepository)

DEFAULT_DB_PATH = os.environ.get("RAID_COACH_DB", "data/raid_coach.db")


class Store:
    """Database + repositories used by the write endpoints."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = Database(db_path)
        self.metrics = MetricsRepository(self.db)
        self.sessions = SessionRepository(self.db)
        self.benchmarks = BenchmarkRepository(self.db)
        self.athlete_id = self._ensure_default_athlete()

    def _ensure_default_athlete(self) -> int:
        rows = self.db.query("SELECT id FROM athlete_profiles ORDER BY id LIMIT 1")
        if rows:
            return rows[0]["id"]
        user_id = self.db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("athlete@raid-coach.local", "!local-single-user")).lastrowid
        return self.db.execute(
            """INSERT INTO athlete_profiles (user_id, name, main_goal, goal_date)
               VALUES (?, ?, ?, ?)""",
            (user_id, "Athlète RAID", "RAID selection 2029", "2029-03-01")).lastrowid
