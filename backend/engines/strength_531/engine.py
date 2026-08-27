"""Force 5/3/1 (Mission 4) — Push/Pull/Legs, Big 3 McGill, finisher WOD.

Training Max = 90% du 1RM. Cycle 4 semaines (5/5/5+, 3/3/3+, 5/3/1+, deload).
Progression : +2,5 kg TM haut du corps, +5 kg TM bas du corps par cycle.
Sciatique L5-S1 : deadlift lourd banni → hip thrust / trap-bar ; Big 3 McGill
obligatoire en échauffement ; finisher WOD non lombaire.
"""
from __future__ import annotations

from engines.wod_generator import generate_wod
from engines.wod_generator.generator import FORMAT_CYCLE

DAYS = ["push", "pull", "legs"]

# Séance COMBINÉE haut du corps (2 mouvements principaux). En grande semaine il
# n'y a que 2 jours OFF pour 3 groupes : sauter un groupe laissait une semaine
# entière sans tirage (ou sans poussée), ce qui casse la progression 5/3/1.
# Avec « upper » = développé couché + rowing, les 3 patterns passent CHAQUE
# semaine, sans jamais placer de force un jour de service.
COMBO_DAYS = {"upper": ("bench", "row")}

# Position dans la rotation des finishers. `upper` remplace `push` la semaine où
# il apparaît (les deux ne coexistent jamais) → pas de collision d'index.
_ROT_IDX = {"push": 0, "pull": 1, "legs": 2, "upper": 0, "fullbody": 1}

# 1RM réels (estimés du niveau actuel) → Training Max (90%, arrondi 2,5 kg).
# Niveau actuel : DC 4×8 @75kg (1RM ~100), Squat 4×5 @100kg (1RM ~117).
# Objectifs : DC 140 kg, Squat 160 kg.
TRAINING_MAX = {
    "bench": {"name": "Développé couché", "tm": 90.0, "inc": 2.5, "goal_1rm": 140},   # 1RM ~100
    "squat": {"name": "Squat", "tm": 105.0, "inc": 5.0, "goal_1rm": 160},             # 1RM ~117
    "ohp": {"name": "Presse militaire", "tm": 57.5, "inc": 2.5, "goal_1rm": 80},      # 1RM ~64
    "row": {"name": "Rowing barre", "tm": 92.5, "inc": 2.5, "goal_1rm": 120},         # 1RM ~103
}

_MAIN_BY_DAY = {"push": "bench", "pull": "row", "legs": "squat"}

# Schéma 5/3/1 : (pct du TM, reps) — dernière série AMRAP ("+")
_WEEK_SCHEME = {
    1: [(65, "5"), (75, "5"), (85, "5+")],
    2: [(70, "3"), (80, "3"), (90, "3+")],
    3: [(75, "5"), (85, "3"), (95, "1+")],
    4: [(50, "5"), (60, "5"), (70, "5")],   # deload (relevé pour rester qualitatif)
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
        ("Soulevé de terre trap-barre", 4, "6-8", 100, "2-0-1", 120),
        ("Hip thrust (remplace deadlift lourd)", 4, "10", 80, "2-1-1", 90),
        ("Fentes haltères / côté", 4, "10", 18, "2-0-1", 90),
        ("Leg curl", 4, "12", 30, "2-1-1", 60),
    ],
}

# ---- Bibliothèque FULL BODY (mouvements variés, tournants par séance) ----
# (nom, lift de référence pour la charge | None, facteur du TM, séries, reps, repos s)
_FB_LOWER = [
    ("Back squat", "squat", 1.00, 5, "6", 180),
    ("Front squat (barre)", "squat", 0.82, 4, "6-8", 150),
    ("Soulevé de terre trap-barre", "squat", 1.10, 5, "5", 180),
    ("Box squat", "squat", 0.90, 5, "5", 150),
    ("Goblet squat (haltère)", "squat", 0.55, 4, "10-12", 90),
]
_FB_PUSH = [
    ("Développé couché (barre)", "bench", 1.00, 5, "6", 180),
    ("Développé incliné haltères", "bench", 0.68, 4, "8-10", 120),
    ("Presse militaire debout (barre)", "ohp", 1.00, 4, "6-8", 150),
    ("Développé militaire haltères", "ohp", 0.72, 4, "8-10", 120),
    ("Dips lestés", None, 0.0, 4, "8-12", 120),
]
_FB_PULL = [
    ("Rowing barre buste penché", "row", 1.00, 4, "8-10", 120),
    ("Tractions pronation", None, 0.0, 4, "8-12", 120),
    ("Tractions supination", None, 0.0, 4, "8-12", 120),
    ("Tirage horizontal poulie", "row", 0.85, 4, "10-12", 90),
    ("Tirage vertical poulie", None, 0.0, 4, "10", 90),
]
_FB_ACC = [
    ("Fentes avant haltères", None, 0.0, 3, "12 / jambe", 75),
    ("Hip thrust", None, 0.0, 3, "12", 75),
    ("Leg curl", None, 0.0, 3, "15", 60),
    ("Split squat bulgare", None, 0.0, 3, "10 / jambe", 75),
    ("Élévations latérales", None, 0.0, 3, "15", 45),
    ("Curl haltères", None, 0.0, 3, "12", 60),
    ("Curl marteau", None, 0.0, 3, "12", 60),
    ("Gainage Pallof press", None, 0.0, 3, "12 / côté", 45),
    ("Dips", None, 0.0, 3, "max", 60),
]


def _fb_move(entry, cycle: int, base: dict, is_deload: bool) -> dict:
    name, blift, factor, sets, reps, rest = entry
    load = None
    if blift and blift in base:
        tm = _tm_for(blift, cycle, base)
        load = _round25(factor * tm * (0.85 if is_deload else 1.0))
    if is_deload:
        sets = max(2, sets - 1)
    return {"name": name, "sets": sets, "reps": reps,
            "load_kg": load, "rest_sec": rest}


def _fullbody_movements(week: int, cycle: int, base: dict, variant: int) -> list[dict]:
    """Sélection tournante : lower + push + pull + 2 accessoires variés, décalés
    par (cycle, semaine, variant) → deux séances full body ne sont pas pareilles."""
    is_deload = week == 4
    k = cycle * 4 + (week - 1) + int(variant)
    lower = _FB_LOWER[k % len(_FB_LOWER)]
    push = _FB_PUSH[(k + 1) % len(_FB_PUSH)]
    pull = _FB_PULL[(k + 2) % len(_FB_PULL)]
    a = _FB_ACC[(k + 3) % len(_FB_ACC)]
    b = _FB_ACC[(k + 3 + 4) % len(_FB_ACC)]
    if b is a:
        b = _FB_ACC[(k + 3 + 5) % len(_FB_ACC)]
    return [_fb_move(m, cycle, base, is_deload) for m in (lower, push, pull, a, b)]


def _round25(x: float) -> float:
    return round(x / 2.5) * 2.5


def resolve_maxes(maxes: dict | None = None) -> dict:
    """Fusionne les 1RM par utilisateur dans la structure TRAINING_MAX.
    `maxes` = {lift: 1RM_kg}. TM = 90% du 1RM (arrondi 2,5 kg). Les lifts absents
    gardent les valeurs par défaut."""
    base = {k: dict(v) for k, v in TRAINING_MAX.items()}
    for lift, one_rm in (maxes or {}).items():
        if lift in base and one_rm:
            base[lift] = {**base[lift], "tm": _round25(0.9 * float(one_rm))}
    return base


def _tm_for(lift: str, cycle: int, base: dict | None = None) -> float:
    b = (base or TRAINING_MAX)[lift]
    return b["tm"] + max(0, cycle) * b["inc"]


def _main_lift(lift: str, week: int, cycle: int, base: dict | None = None) -> dict:
    base = base or TRAINING_MAX
    tm = _tm_for(lift, cycle, base)
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
    return {"lift": lift, "name": base[lift]["name"], "training_max": tm,
            "sets": sets, "note": note}


def _accessories_from(rows) -> list[dict]:
    out = []
    for name, sets, reps, load, tempo, rest in rows:
        prog = (f"objectif {load + 2.5}kg quand {sets}×{reps.split('-')[-1]} atteint"
                if load else "progresser en reps puis en difficulté")
        out.append({"name": name, "sets": sets, "reps": reps,
                    "load_kg": load or None, "tempo": tempo, "rest_sec": rest,
                    "notes": f"double progression — {prog}"})
    return out


def _accessories(day: str) -> list[dict]:
    if day in COMBO_DAYS:
        # Séance combinée : on garde 2 accessoires de chaque groupe pour tenir
        # dans la même durée qu'une séance simple (2 mouvements principaux).
        rows = _ACCESSORIES["push"][:2] + _ACCESSORIES["pull"][:2]
        return _accessories_from(rows)
    return _accessories_from(_ACCESSORIES[day])


def _finisher(day: str, week: int, cycle: int) -> dict:
    """WOD court non lombaire, qui ne retape pas les mêmes muscles que le jour.

    Le format suit la ROTATION (variety_index) et non un tirage aléatoire :
    d'une séance de force à la suivante (push → pull → legs → semaine
    suivante…) l'index avance de 1, donc le format change à chaque fois et les
    15 formats défilent. La durée alterne aussi (10/12 min, 8 en deload) pour
    que deux finishers ne se ressemblent pas.
    """
    idx = (cycle * 4 + (week - 1)) * len(DAYS) + _ROT_IDX.get(day, 0)
    fmt = FORMAT_CYCLE[idx % len(FORMAT_CYCLE)]
    # Les builders respectent désormais la durée demandée → la fenêtre 8-12 min
    # d'un finisher est garantie quel que soit le format tiré.
    dur = 8 if week == 4 else (10 if idx % 2 == 0 else 12)
    wod = generate_wod(fmt=fmt, duration_min=dur,
                       seed=f"finisher_{day}_{week}_{cycle}", exclude_lumbar=True)
    wod["role"] = "finisher musculation (8-12 min, non lombaire)"
    return wod


def generate_strength_531(day: str, week: int = 1, cycle: int = 0,
                          maxes: dict | None = None, variant: int = 0) -> dict:
    if day not in DAYS and day != "fullbody" and day not in COMBO_DAYS:
        raise ValueError(
            f"jour inconnu: {day} (attendus: {', '.join(DAYS)}, "
            f"{', '.join(COMBO_DAYS)}, fullbody)")
    week = max(1, min(int(week), 4))
    cycle = max(0, int(cycle))
    base = resolve_maxes(maxes)

    if day == "fullbody":
        # Séance ~60-75 min, tout le corps, MOUVEMENTS VARIÉS d'une séance à l'autre.
        movements = _fullbody_movements(week, cycle, base, variant)
        return {
            "day": "fullbody", "week": week, "cycle": cycle, "is_deload": week == 4,
            "warmup_mcgill": _MCGILL,
            "movements": movements,           # liste détaillée (séries × reps · repos · charge)
            "notes": [
                "Full body : ~60-75 min, récup complète sur les gros mouvements.",
                "Big 3 McGill à l'échauffement. Charges auto d'après tes 1RM.",
                "Progresse en charge (gros mouvements) puis en reps (accessoires).",
            ],
        }

    lifts = COMBO_DAYS[day] if day in COMBO_DAYS else (_MAIN_BY_DAY[day],)
    mains = [_main_lift(lift, week, cycle, base) for lift in lifts]
    notes = [
        "Big 3 McGill obligatoire en échauffement de TOUTE séance force.",
        "Dernière série du mouvement principal en AMRAP (sauf deload).",
    ]
    if len(mains) > 1:
        notes.insert(0, "Séance HAUT DU CORPS : deux mouvements principaux "
                        f"({' + '.join(m['name'] for m in mains)}) — alterner "
                        "les séries lourdes, récup complète entre les deux.")
    session = {
        "day": day,
        "week": week,
        "cycle": cycle,
        "is_deload": week == 4,
        "warmup_mcgill": _MCGILL,
        "main_lift": mains[0],          # compat clients existants
        "main_lifts": mains,
        "accessories": _accessories(day),
        "finisher_wod": _finisher(day, week, cycle),
        "notes": notes,
    }
    if day == "pull":
        max_pullups = 16
        session["grease_the_groove"] = (
            f"Tractions GtG : séries de {max_pullups // 2} (50% du max {max_pullups}), "
            "plusieurs fois dans la journée, jamais à l'échec — HORS séance.")
    return session


def build_cycle_overview(cycle: int = 0, maxes: dict | None = None) -> dict:
    """Vue d'ensemble du cycle 4 semaines × 3 jours + Training Max courants."""
    base = resolve_maxes(maxes)
    weeks = {}
    for w in range(1, 5):
        weeks[w] = {d: generate_strength_531(d, w, cycle, maxes)["main_lift"]["sets"] for d in DAYS}
    return {
        "cycle": cycle,
        "training_max": {k: _tm_for(k, cycle, base) for k in base},
        "next_cycle_progression": {k: base[k]["inc"] for k in base},
        "weeks": weeks,
    }


def build_progression(lift: str, cycles: int = 6, maxes: dict | None = None) -> dict:
    """Projection de la charge sur N cycles (top set semaine 3 = 95% TM) + e1RM estimé."""
    resolved = resolve_maxes(maxes)
    if lift not in resolved:
        raise ValueError(f"mouvement inconnu: {lift} (attendus: {', '.join(resolved)})")
    base = resolved[lift]
    points = []
    for c in range(max(1, min(cycles, 24))):
        tm = base["tm"] + c * base["inc"]
        points.append({
            "cycle": c,
            "training_max": tm,
            "top_set_kg": _round25(tm * 0.95),   # série lourde S3
            "est_1rm": round(tm / 0.9),          # TM = 90% du 1RM
        })
    return {"lift": lift, "name": base["name"], "increment": base["inc"],
            "goal_1rm": base.get("goal_1rm"), "points": points}
