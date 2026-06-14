"""Bibliothèque de mouvements CrossFit — charges/distances/reps FIXES, taggées.

Chaque mouvement : catégorie (gym/weightlifting/cardio), pattern (push/pull/legs/
core/cardio), unité de mesure, charge fixe éventuelle, et flag `lumbar` (risque
lombaire — exclu si exclude_lumbar, jamais en dernière position d'un WOD long).
Charges calées ~70-80% de la capacité de l'athlète (conditioning, pas de 1RM).
"""
from __future__ import annotations

# unit : reps | cal | m_cardio | m_run | m_carry | s
def M(mid, name, cat, pattern, unit, load=None, lumbar=False):
    return {"id": mid, "name": name, "cat": cat, "pattern": pattern,
            "unit": unit, "load": load, "lumbar": lumbar}


MOVEMENTS = [
    # --- GYMNASTICS ---
    M("pullup", "tractions", "gym", "pull", "reps"),
    M("c2b", "tractions poitrine-barre", "gym", "pull", "reps"),
    M("muscleup", "muscle-ups barre", "gym", "pull", "reps"),
    M("t2b", "toes-to-bar", "gym", "core", "reps"),
    M("k2e", "knees-to-elbows", "gym", "core", "reps"),
    M("hspu", "handstand push-ups", "gym", "push", "reps"),
    M("ringdip", "dips anneaux", "gym", "push", "reps"),
    M("bardip", "dips barre", "gym", "push", "reps"),
    M("pushup", "pompes", "gym", "push", "reps"),
    M("hswalk", "handstand walk", "gym", "push", "m_carry"),
    M("pistol", "pistols (1 jambe)", "gym", "legs", "reps"),
    M("boxjump", "box jumps (60cm)", "gym", "legs", "reps"),
    M("boxover", "box step-overs", "gym", "legs", "reps"),
    M("airsquat", "air squats", "gym", "legs", "reps"),
    M("burpee", "burpees", "gym", "cardio", "reps"),
    M("bfburpee", "bar-facing burpees", "gym", "cardio", "reps"),
    M("du", "double-unders", "gym", "cardio", "reps"),
    M("lsit", "L-sit", "gym", "core", "s"),
    M("ropeclimb", "montées de corde 5m", "gym", "pull", "reps"),
    # --- HALTÉROPHILIE / FORCE (charges fixes) ---
    M("wallball", "wall balls (9kg, 3m)", "wl", "legs", "reps", load=9),
    M("thruster", "thrusters", "wl", "legs", "reps", load=42.5),
    M("frontsquat", "front squats", "wl", "legs", "reps", load=70),
    M("ohs", "overhead squats", "wl", "legs", "reps", load=50),
    M("pushpress", "push press", "wl", "push", "reps", load=60),
    M("benchpress", "développé couché", "wl", "push", "reps", load=70),
    M("kbswing", "kettlebell swings (24kg)", "wl", "pull", "reps", load=24),
    M("dbsnatch", "DB snatch (22.5kg)", "wl", "pull", "reps", load=22.5),
    M("dbthruster", "DB thrusters (2×22.5kg)", "wl", "legs", "reps", load=22.5),
    M("farmer", "farmer carry (2×32kg)", "wl", "core", "m_carry", load=32),
    M("powerclean", "power cleans", "wl", "pull", "reps", load=70, lumbar=True),
    M("snatch", "snatch barre", "wl", "pull", "reps", load=50, lumbar=True),
    M("deadlift", "deadlifts", "wl", "legs", "reps", load=100, lumbar=True),
    M("sandbag", "sandbag carry (40kg)", "wl", "core", "m_carry", load=40, lumbar=True),
    # --- MACHINES CARDIO (valeurs fixes) ---
    M("assault", "cal Assault bike", "cardio", "cardio", "cal"),
    M("echo", "cal Echo bike", "cardio", "cardio", "cal"),
    M("row", "rameur", "cardio", "cardio", "m_cardio"),
    M("ski", "ski erg", "cardio", "cardio", "m_cardio"),
    M("run", "course", "cardio", "cardio", "m_run"),
]

BY_ID = {m["id"]: m for m in MOVEMENTS}


def pool(exclude_lumbar: bool = True) -> list[dict]:
    return [m for m in MOVEMENTS if not (exclude_lumbar and m["lumbar"])]
