"""BUILD 13 — Database access layer (bi-backend).

- Par défaut : **SQLite** (stdlib) — local, sandbox, tests.
- Si `DATABASE_URL` (postgres) est défini : **PostgreSQL** via psycopg2 + pool de
  connexions (production Render/Railway → données persistantes).

La couche repository reste inchangée : SQL paramétré avec des `?`, traduits en
`%s` pour PostgreSQL. Le DDL canonique (schema.py) est traduit à la volée
(SERIAL, now(), TIMESTAMPTZ). Les INSERT obtiennent leur id via `RETURNING id`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Any

from .schema import SCHEMA_SQL, TABLES


class _Result:
    """Retour unifié de execute() : expose .lastrowid quel que soit le backend."""
    __slots__ = ("lastrowid",)

    def __init__(self, lastrowid: int | None = None) -> None:
        self.lastrowid = lastrowid


def pg_translate_sql(sql: str) -> str:
    """Traduit le SQL paramétré (SQLite) vers PostgreSQL. Notre SQL ne contient
    ni '?' ni '%' littéraux dans des chaînes → substitution sûre."""
    return sql.replace("?", "%s").replace("datetime('now')", "now()")


def pg_translate_ddl(sql: str) -> str:
    """Traduit le DDL canonique SQLite → PostgreSQL."""
    return (sql
            .replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
            .replace("datetime('now')", "now()")
            .replace("TEXT NOT NULL DEFAULT (now())", "TIMESTAMPTZ NOT NULL DEFAULT now()"))


def _is_plain_insert(sql: str) -> bool:
    s = sql.lstrip().lower()
    return s.startswith("insert") and "returning" not in s


class Database:
    def __init__(self, path: str = ":memory:", url: str | None = None) -> None:
        url = url if url is not None else os.environ.get("DATABASE_URL", "")
        self.is_postgres = url.startswith(("postgres://", "postgresql://"))
        self._lock = threading.Lock()
        if self.is_postgres:
            self._init_postgres(url)
        else:
            self._init_sqlite(path)

    # ---------- SQLite ----------
    def _init_sqlite(self, path: str) -> None:
        # check_same_thread=False + lock : FastAPI exécute les endpoints sync
        # dans un threadpool, la connexion doit être partageable entre threads.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(SCHEMA_SQL)
            self.conn.commit()

    # ---------- PostgreSQL ----------
    def _init_postgres(self, url: str) -> None:
        import psycopg2  # noqa: F401  (présent via psycopg2-binary)
        from psycopg2.pool import ThreadedConnectionPool
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        self.pool = ThreadedConnectionPool(1, 10, dsn=url)
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(pg_translate_ddl(SCHEMA_SQL))
            conn.commit()
        finally:
            self.pool.putconn(conn)

    def _pg_run(self, sql: str, params: tuple, fetch: bool):
        from psycopg2.extras import RealDictCursor
        q = pg_translate_sql(sql)
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if not fetch and _is_plain_insert(q):
                    q = q.rstrip().rstrip(";") + " RETURNING id"
                    cur.execute(q, params)
                    row = cur.fetchone()
                    conn.commit()
                    return _Result(row["id"] if row else None)
                cur.execute(q, params)
                rows = cur.fetchall() if fetch else []
                conn.commit()
                return rows if fetch else _Result(None)
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    # ---------- Interface unifiée ----------
    def execute(self, sql: str, params: tuple = ()) -> _Result:
        if self.is_postgres:
            return self._pg_run(sql, params, fetch=False)
        with self._lock:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return _Result(cur.lastrowid)

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        if self.is_postgres:
            return [dict(r) for r in self._pg_run(sql, params, fetch=True)]
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def tables(self) -> list[str]:
        if self.is_postgres:
            rows = self.query(
                "SELECT table_name AS name FROM information_schema.tables "
                "WHERE table_schema = 'public'")
        else:
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
