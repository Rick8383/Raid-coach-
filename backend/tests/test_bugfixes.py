"""Tests de régression — bugs identifiés et corrigés lors de l'audit du 12/06/2026.

Chaque test correspond à un bug confirmé ; il échoue sur le code d'avant-correction.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import Database
from db.repositories.repositories import AthleteRepository, MetricsRepository
from engines.nutrition import ActivityLevel, NutritionPhase, NutritionProfile, NutritionService
from engines.run_engine.readiness_engine import readiness_score, readiness_zone
from engines.selection_wods import SelectionWODGenerator
from engines.strength.pr_engine import PREngine


# Bug 1 — connexion SQLite inutilisable depuis le threadpool FastAPI
def test_database_usable_across_threads():
    db = Database(":memory:")
    errors: list[Exception] = []

    def writer(i: int):
        try:
            db.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                       (f"t{i}@t.t", "x"))
            db.query("SELECT * FROM users")
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors


# Bug 2 — readiness du run_engine : fatigue/stress doivent être inversés
def test_readiness_exhausted_athlete_is_red():
    assert readiness_zone(readiness_score(30, 95, 90, 40, 20)).value == "red"


def test_readiness_fresh_athlete_is_green():
    assert readiness_zone(readiness_score(80, 20, 20, 80, 80)).value == "green"


def test_readiness_decreases_with_fatigue():
    fresh = readiness_score(70, 10, 30, 70, 70)
    tired = readiness_score(70, 90, 30, 70, 70)
    assert tired < fresh


# Bug 3 — run_elite importable seul (plus de sys.path /tmp)
def test_run_elite_importable_standalone():
    import subprocess
    result = subprocess.run(
        [sys.executable, "-c", "import engines.run_elite"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# Bug 4 — profils extrêmes : macros clampées, jamais d'exception
def test_nutrition_extreme_profiles_do_not_raise():
    service = NutritionService()
    light = NutritionProfile(40, 140, 30, "f", None, 40, NutritionPhase.RECOMP)
    heavy = NutritionProfile(180, 220, 14, "m", None, 180, NutritionPhase.BUILD)
    t1 = service.daily(light, ActivityLevel.REST)
    t2 = service.daily(heavy, ActivityLevel.EXTREME)
    assert 1200 <= t1.calories <= 6000
    assert 1200 <= t2.calories <= 6000


# Bug 6 — e1RM : plus de singularité Brzycki sur les séries longues
def test_e1rm_high_reps_stays_plausible():
    assert PREngine.e1rm(100, 30) == pytest.approx(200, abs=1)  # Epley seul
    assert PREngine.e1rm(100, 36) < 250
    # continuité raisonnable autour du seuil de 12 reps
    assert abs(PREngine.e1rm(100, 12) - PREngine.e1rm(100, 13)) < 10


# Bug 8 — noms de colonnes inconnus rejetés avant interpolation SQL
def test_repositories_reject_unknown_columns():
    db = Database(":memory:")
    athletes = AthleteRepository(db)
    uid = athletes.create_user("a@a.a", "x")
    with pytest.raises(ValueError, match="unknown"):
        athletes.create_profile(uid, "X", **{"name) VALUES(0); --": 1})
    aid = athletes.create_profile(uid, "X", weight_kg=75)
    with pytest.raises(ValueError, match="unknown"):
        athletes.update_profile(aid, **{"weight_kg = 0; --": 1})
    metrics = MetricsRepository(db)
    with pytest.raises(ValueError, match="unknown"):
        metrics.upsert(aid, "2026-06-12", **{"evil); --": 1})


# Bug 9 — anti-répétition WOD bornée (plus de RecursionError)
def test_wod_variant_anticollision_is_bounded():
    gen = SelectionWODGenerator()
    history: list[str] = []
    for _ in range(80):  # bien au-delà de la borne de 50 essais
        wod = gen.death_by_variant("seed", history)
        history.append(wod.wod_id)
    assert len(history) == 80  # aucune exception levée


def test_wod_variant_avoids_recent_ids():
    gen = SelectionWODGenerator()
    first = gen.death_by_variant("seed")
    second = gen.death_by_variant("seed", [first.wod_id])
    assert second.wod_id != first.wod_id
