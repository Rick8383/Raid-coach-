"""BUILD 13 — Database access layer.

Production: PostgreSQL via DATABASE_URL (SQLAlchemy engine in db/orm_models.py).
Local/sandbox/tests: SQLite (stdlib) executing the same canonical schema.
The repository layer below is backend-agnostic (raw SQL, parameterized)."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from .schema import SCHEMA_SQL, TABLES


class Database:
    def __init__(self, path: str = ":memory:") -> None:
        # check_same_thread=False + lock : FastAPI exécute les endpoints sync
        # dans un threadpool, la connexion doit être partageable entre threads.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self.conn.executescript(SCHEMA_SQL)
            self.conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def tables(self) -> list[str]:
        rows = self.query("SELECT name FROM sqlite_master WHERE type='table'")
        return sorted(r["name"] for r in rows)


class CacheLayer:
    """Redis-compatible interface. Production: redis.Redis. Sandbox: in-memory TTL dict.
    Swap by passing a real redis client with get/setex/delete."""

    def __init__(self, redis_client: Any = None) -> None:
        self.redis = redis_client
        self._mem: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> dict | None:
        if self.redis:
            raw = self.redis.get(key)
            return json.loads(raw) if raw else None
        item = self._mem.get(key)
        if not item:
            return None
        expires, raw = item
        if time.time() > expires:
            del self._mem[key]
            return None
        return json.loads(raw)

    def set(self, key: str, value: dict, ttl_sec: int = 3600) -> None:
        raw = json.dumps(value)
        if self.redis:
            self.redis.setex(key, ttl_sec, raw)
        else:
            self._mem[key] = (time.time() + ttl_sec, raw)

    def invalidate(self, key: str) -> None:
        if self.redis:
            self.redis.delete(key)
        self._mem.pop(key, None)


# Cache TTL policy (from Master Plan)
CACHE_TTL = {
    "coach_decision": 3600,      # 1h
    "athlete_profile": 900,      # 15min
    "analytics_recent": 1800,    # 30min
}
