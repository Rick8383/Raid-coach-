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
    """Une séance de force est toujours accompagnée d'une séance le matin."""
    for d, day in _days(12):
        main = [s for s in day["sessions"] if s["type"] != "recovery"]
        if any(s["type"] == "strength" for s in main):
            assert len(main) >= 2, f"force en séance isolée : {d}"
            assert any(s["type"] in ("run", "crossfit") for s in main)


def test_push_pull_legs_stay_balanced():
    """Les 3 groupes passent le même nombre de fois (±1) sur 12 semaines."""
    lifts = Counter()
    for _d, day in _days(12):
        for s in day["sessions"]:
            if s["type"] == "strength":
                lifts[s["title"].split("—")[0].strip()] += 1
    assert set(lifts) == {"Force PUSH", "Force PULL", "Force LEGS"}
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
    assert len(fmts) >= 8
    assert all(a != b for a, b in zip(fmts, fmts[1:])), fmts
    assert len(set(fmts)) >= 8, "au moins 8 formats distincts sur 12 semaines"


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
