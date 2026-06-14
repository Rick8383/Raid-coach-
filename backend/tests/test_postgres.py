"""Tests de la couche PostgreSQL (BUILD 13 bi-backend).

- Traduction SQL/DDL : fonctions pures, testées partout.
- Intégration : exécutée seulement si DATABASE_URL est défini (job CI Postgres),
  sinon ignorée (le reste de la suite couvre SQLite).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import pg_translate_ddl, pg_translate_sql, _is_plain_insert


def test_translate_sql_placeholders_and_now():
    assert pg_translate_sql("SELECT * FROM t WHERE id = ?") == "SELECT * FROM t WHERE id = %s"
    assert "now()" in pg_translate_sql("UPDATE t SET u = datetime('now') WHERE id = ?")
    assert "%s" in pg_translate_sql("UPDATE t SET u = datetime('now') WHERE id = ?")


def test_translate_ddl_serial_and_timestamptz():
    ddl = pg_translate_ddl(
        "CREATE TABLE x (id INTEGER PRIMARY KEY, "
        "created_at TEXT NOT NULL DEFAULT (datetime('now')))")
    assert "SERIAL PRIMARY KEY" in ddl
    assert "TIMESTAMPTZ NOT NULL DEFAULT now()" in ddl
    assert "datetime('now')" not in ddl


def test_is_plain_insert_detection():
    assert _is_plain_insert("INSERT INTO t (a) VALUES (%s)")
    assert _is_plain_insert("  insert into t (a) values (%s) on conflict(a) do update set a=excluded.a")
    assert not _is_plain_insert("INSERT INTO t (a) VALUES (%s) RETURNING id")
    assert not _is_plain_insert("UPDATE t SET a = %s")
    assert not _is_plain_insert("SELECT * FROM t")


# ---------- Intégration PostgreSQL (CI uniquement) ----------
_PG = os.environ.get("DATABASE_URL", "")
pg_only = pytest.mark.skipif(
    not _PG.startswith(("postgres://", "postgresql://")),
    reason="DATABASE_URL PostgreSQL non défini")


@pg_only
def test_postgres_store_end_to_end():
    """Crée le schéma, seed l'athlète, écrit/relit métriques et séances sur PG réel."""
    from api.persistence import Store
    store = Store(":memory:")  # url pris depuis DATABASE_URL → PG
    assert store.db.is_postgres
    assert "garmin_tokens" in store.db.tables()

    # athlète seedé + maxes
    prof = store.profile_payload()
    assert prof["current"].get("pullups_max") == 16

    # upsert métrique (HRV/sommeil)
    store.metrics.upsert(store.athlete_id, "2027-01-02", readiness=72, hrv=68, resting_hr=47)
    latest = store.metrics.latest(store.athlete_id)
    assert latest["hrv"] == 68

    # séance planifiée → historique
    sid = store.sessions.record(store.athlete_id, "run", "2027-01-03", 60, 7, 29.4,
                                {"k": "v"}, status="planned", family_id="Test Run")
    assert isinstance(sid, int)
    rows = store.sessions.last_n(store.athlete_id, 10)
    assert any(s["session_date"] == "2027-01-03" for s in rows)
