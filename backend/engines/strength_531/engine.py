"""Force 5/3/1 (Mission 4) — Push/Pull/Legs, Big 3 McGill, finisher WOD.

Training Max = 90% du 1RM. Cycle 4 semaines (5/5/5+, 3/3/3+, 5/3/1+, deload).
Progression : +2,5 kg TM haut du corps, +5 kg TM bas du corps par cycle.
Sciatique L5-S1 : deadlift lourd banni → hip thrust / trap-bar ; Big 3 McGill
obligatoire en échauffement ; finisher WOD non lombaire.
"""
from __future__ import annotations

from engines.wod_generator import generate_wod

DAYS = ["push", "pull", "legs"]

# 1RM réels → Training Max (90%, arrondi 2,5 kg) + incrément par cycle
TRAINING_MAX = {
    "bench": {"name": "Développé couché", "tm": 85.0, "inc": 2.5},     # 1RM 95
    "squat": {"name": "Squat", "tm": 100.0, "inc": 5.0},               # 1RM 110
    "ohp": {"name": "Presse militaire", "tm": 54.0, "inc": 2.5},       # 1RM ~60
    "row": {"name": "Rowing barre", "tm": 90.0, "inc": 2.5},           # 1RM ~100
}

_MAIN_BY_DAY = {"push": "bench", "pull": "row", "legs": "squat"}

# Schéma 5/3/1 : (pct du TM, reps) — dernière série AMRAP ("+")
_WEEK_SCHEME = {
    1: [(65, "5"), (75, "5"), (85, "5+")],
    2: [(70, "3"), (80, "3"), (90, "3+")],
    3: [(75, "5"), (85, "3"), (95, "1+")],
    4: [(40, "5"), (50, "5"), (60, "5")],   # deload
}

_MCGILL = [
    {"name": "Cat-camel (mobilité)", "prescription": "1 × 8 lent"},
    {"name": "Curl-up McGill", "prescription": "pyramide 6/4/2 × 10s", "notes": "dos neutre, jamais à l'échec"},
    {"name": "Side plank", "prescription": "pyramide 6/4/2 × 10s"},
    {"name": "Bird dog", "prescription": "pyramide 6/4/2 × 10s"},
]

# Accessoires par jour (double progression : monter les reps puis +2,5 kg)
_ACCESSORIES = {
    "push": [
        ("Développé incliné haltères", 4, "6-8", 34, "2-0-1", 90),
        ("Dips lestés", 4, "10-12", 12, "2-0-1", 90),
        ("Écarté incliné / peck deck", 3, "15", 14, "2-1-1", 60),
        ("Barre au front", 3, "8-10", 30, "2-0-1", 75),
        ("Extension poulie pronation", 3, "8-12", 20, "2-0-1", 60),
        ("Pompes mains serrées", 3, "max", 0, "contrôlé", 60),
    ],
    "pull": [
        ("Tirage vertical", 4, "8", 80, "2-0-1", 90),
        ("Tirage horizontal", 4, "10", 100, "2-0-1", 90),
        ("Curl barre", 3, "8", 28, "2-0-1", 75),
        ("Curl marteau", 3, "8", 14, "2-0-1", 60),
        ("Curl pupitre haltère", 3, "8", 16, "2-1-1", 60),
    ],
    "legs": [
        ("Hip thrust (remplace deadlift lourd)", 4, "10", 80, "2-1-1", 90),
        ("Fentes haltères / côté", 4, "10", 18, "2-0-1", 90),
        ("Leg curl", 4, "12", 30, "2-1-1", 60),
        ("Leg extension", 4, "12", 35, "2-0-1", 60),
    ],
}


def _round25(x: float) -> float:
    return round(x / 2.5) * 2.5


def _tm_for(lift: str, cycle: int) -> float:
    base = TRAINING_MAX[lift]
    return base["tm"] + max(0, cycle) * base["inc"]


def _main_lift(lift: str, week: int, cycle: int) -> dict:
    tm = _tm_for(lift, cycle)
    sets = []
    for pct, reps in _WEEK_SCHEME[week]:
        sets.append({
            "pct_tm": pct, "reps": reps,
            "load_kg": _round25(tm * pct / 100),
            "rest_sec": 180 if week <= 3 else 120,
            "amrap": reps.endswith("+"),
        })
    note = ""
    if lift == "squat":
        note = "Sciatique : profondeur contrôlée, gainage McGill avant ; jamais de flexion lombaire en fatigue."
    return {"lift": lift, "name": TRAINING_MAX[lift]["name"], "training_max": tm,
            "sets": sets, "note": note}


def _accessories(day: str) -> list[dict]:
    out = []
    for name, sets, reps, load, tempo, rest in _ACCESSORIES[day]:
        prog = (f"objectif {load + 2.5}kg quand {sets}×{reps.split('-')[-1]} atteint"
                if load else "progresser en reps puis en difficulté")
        out.append({"name": name, "sets": sets, "reps": reps,
                    "load_kg": load or None, "tempo": tempo, "rest_sec": rest,
                    "notes": f"double progression — {prog}"})
    return out


def _finisher(day: str, week: int, cycle: int) -> dict:
    # WOD court non lombaire, qui ne retape pas les mêmes muscles que le jour
    dur = 8 if week == 4 else 10
    wod = generate_wod(fmt="auto", duration_min=dur,
                       seed=f"finisher_{day}_{week}_{cycle}", exclude_lumbar=True)
    wod["role"] = "finisher musculation (8-12 min, non lombaire)"
    return wod


def generate_strength_531(day: str, week: int = 1, cycle: int = 0) -> dict:
    if day not in DAYS:
        raise ValueError(f"jour inconnu: {day} (attendus: {', '.join(DAYS)})")
    week = max(1, min(int(week), 4))
    cycle = max(0, int(cycle))
    lift = _MAIN_BY_DAY[day]

    session = {
        "day": day,
        "week": week,
        "cycle": cycle,
        "is_deload": week == 4,
        "warmup_mcgill": _MCGILL,
        "main_lift": _main_lift(lift, week, cycle),
        "accessories": _accessories(day),
        "finisher_wod": _finisher(day, week, cycle),
        "notes": [
            "Big 3 McGill obligatoire en échauffement de TOUTE séance force.",
            "Dernière série du mouvement principal en AMRAP (sauf deload).",
        ],
    }
    if day == "pull":
        max_pullups = 16
        session["grease_the_groove"] = (
            f"Tractions GtG : séries de {max_pullups // 2} (50% du max {max_pullups}), "
            "plusieurs fois dans la journée, jamais à l'échec — HORS séance.")
    return session


def build_cycle_overview(cycle: int = 0) -> dict:
    """Vue d'ensemble du cycle 4 semaines × 3 jours + Training Max courants."""
    weeks = {}
    for w in range(1, 5):
        weeks[w] = {d: generate_strength_531(d, w, cycle)["main_lift"]["sets"] for d in DAYS}
    return {
        "cycle": cycle,
        "training_max": {k: _tm_for(k, cycle) for k in TRAINING_MAX},
        "next_cycle_progression": {k: TRAINING_MAX[k]["inc"] for k in TRAINING_MAX},
        "weeks": weeks,
    }
