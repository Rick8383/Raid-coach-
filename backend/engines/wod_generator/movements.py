"""Bibliothèque de mouvements CrossFit — charges/distances/reps FIXES, taggées.

Chaque mouvement : catégorie (gym/weightlifting/cardio), pattern (push/pull/legs/
core/cardio), unité de mesure, charge fixe éventuelle, flag `lumbar` (risque
lombaire) et `band` de reps (high/med/low) pour des volumes COHÉRENTS :
- high  : mouvements légers à haut volume (double-unders 30-50, air squats, wall balls…)
- med   : gym/haltéro modéré (tractions, dips, KB swing, thrusters… 8-15)
- low   : lourd/technique (clean, snatch, HSPU, muscle-up… 3-8)

Pas de mouvement à temps fixe (L-sit retiré) : ces holds vont en accessoires/échauffement.
"""
from __future__ import annotations


# unit : reps | cal | m_cardio | m_run | m_carry   ;  band : high | med | low
def M(mid, name, cat, pattern, unit, load=None, lumbar=False, band="med"):
    return {"id": mid, "name": name, "cat": cat, "pattern": pattern,
            "unit": unit, "load": load, "lumbar": lumbar, "band": band}


MOVEMENTS = [
    # --- GYMNASTICS ---
    M("pullup", "tractions", "gym", "pull", "reps", band="med"),
    M("c2b", "tractions poitrine-barre", "gym", "pull", "reps", band="med"),
    M("muscleup", "muscle-ups barre", "gym", "pull", "reps", band="low"),
    M("t2b", "toes-to-bar", "gym", "core", "reps", band="med"),
    M("k2e", "knees-to-elbows", "gym", "core", "reps", band="med"),
    M("hspu", "handstand push-ups", "gym", "push", "reps", band="low"),
    M("ringdip", "dips anneaux", "gym", "push", "reps", band="med"),
    M("bardip", "dips barre", "gym", "push", "reps", band="med"),
    M("pushup", "pompes", "gym", "push", "reps", band="med"),
    M("hswalk", "handstand walk", "gym", "push", "m_carry"),
    M("pistol", "pistols (1 jambe)", "gym", "legs", "reps", band="med"),
    M("boxjump", "box jumps (60cm)", "gym", "legs", "reps", band="med"),
    M("boxover", "box step-overs", "gym", "legs", "reps", band="med"),
    M("airsquat", "air squats", "gym", "legs", "reps", band="high"),
    M("burpee", "burpees", "gym", "condi", "reps", band="high"),
    M("bfburpee", "bar-facing burpees", "gym", "condi", "reps", band="high"),
    M("du", "double-unders", "gym", "condi", "reps", band="high"),
    M("ropeclimb", "montées de corde 5m", "gym", "pull", "reps", band="low"),
    # --- HALTÉROPHILIE / FORCE (charges fixes) ---
    M("wallball", "wall balls (9kg, 3m)", "wl", "legs", "reps", load=9, band="high"),
    M("thruster", "thrusters", "wl", "legs", "reps", load=42.5, band="med"),
    M("frontsquat", "front squats", "wl", "legs", "reps", load=70, band="low"),
    M("ohs", "overhead squats", "wl", "legs", "reps", load=50, band="low"),
    M("pushpress", "push press", "wl", "push", "reps", load=60, band="low"),
    M("benchpress", "développé couché", "wl", "push", "reps", load=70, band="low"),
    M("kbswing", "kettlebell swings (24kg)", "wl", "pull", "reps", load=24, band="med"),
    M("dbsnatch", "DB snatch (22.5kg)", "wl", "pull", "reps", load=22.5, band="med"),
    M("dbthruster", "DB thrusters (2×22.5kg)", "wl", "legs", "reps", load=22.5, band="med"),
    M("farmer", "farmer carry (2×32kg)", "wl", "core", "m_carry", load=32),
    M("powerclean", "power cleans", "wl", "pull", "reps", load=70, lumbar=True, band="low"),
    M("snatch", "snatch barre", "wl", "pull", "reps", load=50, lumbar=True, band="low"),
    M("deadlift", "deadlifts", "wl", "legs", "reps", load=100, lumbar=True, band="low"),
    M("sandbag", "sandbag carry (40kg)", "wl", "core", "m_carry", load=40, lumbar=True),
    # --- MACHINES CARDIO (valeurs fixes) ---
    M("assault", "cal Assault bike", "cardio", "cardio", "cal"),
    M("echo", "cal Echo bike", "cardio", "cardio", "cal"),
    M("row", "rameur", "cardio", "cardio", "m_cardio"),
    M("ski", "ski erg", "cardio", "cardio", "m_cardio"),
    M("run", "course", "cardio", "cardio", "m_run"),
]

BY_ID = {m["id"]: m for m in MOVEMENTS}

# Machines cardio mises en avant (assault/echo/ski demandés explicitement)
CARDIO_MACHINES = ["assault", "echo", "ski", "row"]


def pool(exclude_lumbar: bool = True, bodyweight: bool = False) -> list[dict]:
    out = [m for m in MOVEMENTS if not (exclude_lumbar and m["lumbar"])]
    if bodyweight:
        # PDC (poids du corps) : gym sans charge, ni machine cardio ni haltéro.
        out = [m for m in out if m["cat"] == "gym" and not m.get("load")]
    return out
