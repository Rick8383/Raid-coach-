"""Variété des WOD + placement de la force sur les jours OFF.

Deux retours terrain :
1. « Les WOD en fin de séance sont toujours du même format » — le tirage
   aléatoire indépendant sur 15 formats produisait des collisions rapprochées.
2. « Les séances push/pull/legs doivent tomber les jours OFF, en double » — en
   service l'athlète ne peut pas toujours s'entraîner, la séance sautait puis
   était rattrapée plus tard, ce qui décalait tout le plan.
"""
import re
from collections import Counter
from datetime import date, timedelta

from engines.strength_531.engine import _finisher
from engines.weekly_plan import build_day
from engines.wod_generator import generate_wod
from engines.wod_generator.generator import FORMAT_CYCLE, WOD_FORMATS

# semaine du 17/08/2026 = PETITE (service mer/jeu) avec cette ancre
CFG = {"type": "police_3223", "anchor_big_week_monday": "2026-08-10"}
START = date(2026, 8, 17)

# Formats intrinsèquement ouverts : « jusqu'à échec », pas de cap chiffré.
_OPEN_ENDED = {"death_by", "death_by_emom"}


def _days(n_weeks: int):
    for i in range(7 * n_weeks):
        d = START + timedelta(days=i)
        yield d, build_day(d, config=CFG)


# ---------- Force : jours OFF uniquement, toujours en double ----------
def test_no_strength_on_service_days():
    for d, day in _days(12):
        if day["is_work_day"]:
            kinds = [s["type"] for s in day["sessions"]]
            assert "strength" not in kinds, f"force un jour de service : {d}"


def test_strength_is_always_a_double_session():
    """La force tombe toujours dans une journée à DEUX séances (jour OFF). En
    grande semaine le jeudi porte deux séances de force distinctes (pull le
    matin, legs le soir) : push/pull/legs ne sont jamais fusionnés."""
    for d, day in _days(12):
        main = [s for s in day["sessions"] if s["type"] != "recovery"]
        if any(s["type"] == "strength" for s in main):
            assert len(main) >= 2, f"force en séance isolée : {d}"
            assert day["is_work_day"] is False


def test_push_pull_legs_stay_balanced():
    """Les 3 patterns passent le même nombre de fois (±1) sur 12 semaines,
    comptés sur les MOUVEMENTS PRINCIPAUX plutôt que sur les titres."""
    lifts = Counter()
    for _d, day in _days(12):
        for s in day["sessions"]:
            if s["type"] == "strength":
                for m in s["detail"].get("main_lifts", []):
                    lifts[m["lift"]] += 1
    assert set(lifts) == {"bench", "row", "squat"}
    assert max(lifts.values()) - min(lifts.values()) <= 1, lifts


def test_current_week_matches_athlete_reality():
    """Petite semaine : push lundi, pull mardi, legs vendredi (jours OFF)."""
    expected = {0: "PUSH", 1: "PULL", 4: "LEGS"}
    for offset, lift in expected.items():
        day = build_day(START + timedelta(days=offset), config=CFG)
        assert day["is_work_day"] is False
        titles = [s["title"] for s in day["sessions"] if s["type"] == "strength"]
        assert titles and lift in titles[0], (offset, titles)


# ---------- Variété des formats ----------
def test_finisher_never_repeats_consecutively():
    seen = []
    for cycle in range(3):
        for week in range(1, 5):
            for day in ("push", "pull", "legs"):
                seen.append(_finisher(day, week, cycle)["format_key"])
    assert all(a != b for a, b in zip(seen, seen[1:])), seen
    assert set(seen) == set(WOD_FORMATS), "la palette complète doit défiler"


def test_plan_wods_never_repeat_consecutively():
    fmts = [s["detail"]["format_key"]
            for _d, day in _days(12)
            for s in day["sessions"]
            if s["type"] == "crossfit" and "format_key" in s["detail"]]
    # 1 WOD autonome par petite semaine (les grandes semaines consacrent leurs
    # 2 jours OFF aux 3 séances de force ; le conditioning y passe par les
    # finishers de 8-12 min).
    assert len(fmts) >= 5
    assert all(a != b for a, b in zip(fmts, fmts[1:])), fmts
    assert len(set(fmts)) >= 5, "des formats variés d'une semaine à l'autre"


def test_finisher_stays_short():
    """Un finisher reste dans la fenêtre 8-12 min, quel que soit le format."""
    for cycle in range(2):
        for week in range(1, 5):
            for day in ("push", "pull", "legs"):
                w = _finisher(day, week, cycle)
                if w["format_key"] in _OPEN_ENDED:
                    continue
                mins = [int(n) for n in re.findall(r"\d+", w["duration_or_cap"])]
                assert mins and max(mins) <= 12, (day, week, cycle, w["duration_or_cap"])


def test_every_format_honours_requested_duration():
    """Les 15 builders respectent la durée demandée (avant : 9 l'ignoraient,
    un « finisher 10 min » pouvait sortir un cap de 20 min)."""
    for fmt in FORMAT_CYCLE:
        for dur in (8, 12, 20):
            w = generate_wod(fmt, dur, seed=f"d{dur}", exclude_lumbar=True)
            assert w["format_key"] == fmt
            if fmt in _OPEN_ENDED:
                continue
            mins = [int(n) for n in re.findall(r"\d+", w["duration_or_cap"])]
            assert mins and max(mins) <= dur, (fmt, dur, w["duration_or_cap"])


def test_variety_index_is_deterministic_and_cycles():
    got = [generate_wod("auto", 12, "s", variety_index=i)["format_key"]
           for i in range(len(FORMAT_CYCLE))]
    assert got == list(FORMAT_CYCLE)
    # un tour complet plus loin → même format (rotation stable)
    assert generate_wod("auto", 12, "s", variety_index=len(FORMAT_CYCLE))["format_key"] == FORMAT_CYCLE[0]


# ---------- Chaque semaine couvre les 3 patterns (push / pull / legs) ----------
def test_every_week_covers_push_pull_legs():
    """Aucune semaine ne doit rester sans tirage (ou sans poussée) : en grande
    semaine, les 2 jours OFF portent push (mer) puis pull + legs (jeu)."""
    for w in range(12):
        monday = START + timedelta(days=7 * w)
        lifts = set()
        for i in range(7):
            day = build_day(monday + timedelta(days=i), config=CFG)
            for s in day["sessions"]:
                if s["type"] == "strength":
                    lifts.update(m["lift"] for m in s["detail"].get("main_lifts", []))
        assert {"bench", "row", "squat"} <= lifts, (monday, lifts)


def test_upper_session_has_two_main_lifts():
    from engines.strength_531 import generate_strength_531
    s = generate_strength_531("upper", week=1, cycle=0)
    lifts = [m["lift"] for m in s["main_lifts"]]
    assert lifts == ["bench", "row"]
    assert s["main_lift"]["lift"] == "bench"          # compat clients existants
    assert s["accessories"] and s["finisher_wod"]


def test_recorded_loads_drive_the_plan():
    """Les charges suivent les séries ENREGISTRÉES : logger rowing 6×90 kg
    (1RM estimé 108) doit alourdir la séance de tirage suivante."""
    from fastapi.testclient import TestClient
    import importlib
    from api import main as api_main
    importlib.reload(api_main)
    c = TestClient(api_main.app)

    from engines.strength_531.engine import TRAINING_MAX
    default_tm = TRAINING_MAX["row"]["tm"]

    c.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2026-08-18",
        "duration_min": 70, "intensity_rpe": 8, "status": "done",
        "title": "Force PULL — S2",
        "performed": {"lift": "Rowing barre", "est_1rm": 108.0,
                      "sets": [{"reps": 6, "load_kg": 90, "top": True}]}})

    # 6×90 kg → 1RM estimé Epley = 108 kg, lu directement depuis les séries.
    assert api_main._logged_e1rm(api_main._aid()).get("row", 0) >= 108.0
    maxes = api_main._strength_maxes()
    assert maxes.get("row", 0) >= 108.0
    # …et la séance de tirage suivante est réellement plus lourde qu'au défaut.
    session = api_main.coach.strength_531("pull", 1, 0, maxes)
    assert session["main_lift"]["training_max"] > default_tm


def test_recorded_loads_read_combined_sessions():
    """Format combiné { lifts: [...] } (séance haut du corps) pris en compte."""
    from fastapi.testclient import TestClient
    import importlib
    from api import main as api_main
    importlib.reload(api_main)
    c = TestClient(api_main.app)

    c.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2026-08-26",
        "duration_min": 70, "intensity_rpe": 8, "status": "done",
        "title": "Force HAUT DU CORPS (push+pull) — S3",
        "performed": {"lifts": [
            {"lift": "Développé couché", "est_1rm": 0,
             "sets": [{"reps": 5, "load_kg": 95, "top": True}]},
            {"lift": "Rowing barre", "est_1rm": 0,
             "sets": [{"reps": 8, "load_kg": 85, "top": True}]}]}})
    maxes = api_main._strength_maxes()
    assert maxes.get("bench", 0) >= 95 * (1 + 5 / 30) - 0.5
    assert maxes.get("row", 0) >= 85 * (1 + 8 / 30) - 0.5


def test_push_and_pull_are_never_merged():
    """Demande explicite : push et pull restent DEUX séances distinctes, même
    les semaines où l'athlète n'a que deux jours OFF."""
    for w in range(12):
        monday = START + timedelta(days=7 * w)
        sessions = []
        for i in range(7):
            day = build_day(monday + timedelta(days=i), config=CFG)
            sessions += [s for s in day["sessions"] if s["type"] == "strength"]
        # aucune séance ne porte deux mouvements principaux
        assert all(len(s["detail"].get("main_lifts", [])) == 1 for s in sessions), monday
        # et les trois séances existent bien, séparément
        mains = [s["detail"]["main_lifts"][0]["lift"] for s in sessions]
        assert sorted(mains) == ["bench", "row", "squat"], (monday, mains)
