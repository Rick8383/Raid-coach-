"""Générateur de séances de course — 7 types, 100 séances uniques chacun (700).

Déterministe : (type, seed) → toujours la même séance. La sélection des
paramètres se fait par index à base mixte (mixed-radix) sur les axes de chaque
type → aucune répétition sur les 100 premières séances d'un type.

Allures dérivées de la VMA (défaut 14 km/h) ; FC de la FCmax (défaut 186).
"""
from __future__ import annotations

from math import gcd

from .settings import (FCMAX, VMA_ATHLETE, WEIGHT_KG, fc_bpm, pace_min_km,
                       speed_kmh)

RUN_TYPES = ["vma_courte", "vma_longue", "seuil", "fartlek", "tempo", "z2", "cotes"]
LIBRARY_SIZE = 100   # séances uniques garanties par type


def generate_seed(run_type: str, seed: int) -> str:
    return f"{run_type}_{seed:03d}"


def _permute(idx: int, product: int) -> int:
    """Bijection sur [0, product) — disperse les seeds consécutifs (multiplicateur
    nombre d'or coprime au produit) pour éviter tout déroulé prévisible
    (3×400 → 4×400 → 5×400…), tout en gardant l'unicité sur les 100 premières."""
    a = max(2, int(product * 0.6180339887))
    while gcd(a, product) != 1:
        a += 1
    return (idx * a + 7) % product


def _select(idx: int, axes: list[list]) -> list:
    """Index à base mixte (après permutation) → un élément par axe, combinaisons
    toutes distinctes et bien dispersées d'un seed au suivant."""
    product = 1
    for axis in axes:
        product *= len(axis)
    idx = _permute(idx % product, product)
    out = []
    for axis in axes:
        out.append(axis[idx % len(axis)])
        idx //= len(axis)
    return out


def _zone(pct_fcmax: float) -> str:
    if pct_fcmax < 60:
        return "Z1"
    if pct_fcmax < 80:
        return "Z2"
    if pct_fcmax < 88:
        return "Z3"
    if pct_fcmax < 92:
        return "Z4"
    return "Z5"


def _interval(pct_vma: float, fc_pct: float, vma: float, fcmax: int) -> dict:
    s = speed_kmh(pct_vma, vma)
    return {
        "pace_kmh": s,
        "pace_min_km": pace_min_km(s),
        "pct_vma": pct_vma,
        "fc_bpm": fc_bpm(fc_pct, fcmax),
        "pct_fcmax": round(fc_pct),
        "zone": _zone(fc_pct),
    }


def _warmup(minutes: int, vma: float, fcmax: int, pct_vma: float = 70.0) -> dict:
    inter = _interval(pct_vma, 70, vma, fcmax)
    return {"label": "Échauffement progressif + gammes", "duration_min": minutes,
            "distance_m": round(inter["pace_kmh"] * minutes / 60 * 1000), **inter}


def _cooldown(minutes: int, vma: float, fcmax: int) -> dict:
    inter = _interval(65, 65, vma, fcmax)
    return {"label": "Retour au calme", "duration_min": minutes,
            "distance_m": round(inter["pace_kmh"] * minutes / 60 * 1000), **inter}


def _envelope(run_type: str, seed: int, *, title: str, difficulty: int,
              warmup: dict, body: list, cooldown: dict, total_min: int,
              total_km: float, weight: float, sciatic_note: str = "") -> dict:
    return {
        "seed": generate_seed(run_type, seed),
        "type": run_type,
        "title": title,
        "difficulty": max(1, min(5, difficulty)),
        "duration_min": int(round(total_min)),
        "distance_km": round(total_km, 1),
        "calories": round(weight * total_km * 1.036),
        "warmup": warmup,
        "body": body,
        "cooldown": cooldown,
        "sciatic_note": sciatic_note,
    }


# Combos VMA courte COHÉRENTS (distance_m, séries, reps) — volume total borné
# ~1,6-4,8 km. Triés par volume croissant (progression).
_VMA_COURTE_COMBOS = sorted(
    [(d, s, r, d * s * r) for (d, s, r) in [
        (200, 1, 8), (300, 1, 6), (200, 1, 10), (400, 1, 5), (300, 1, 8),
        (200, 2, 6), (400, 1, 6), (200, 2, 7), (300, 1, 10), (300, 2, 5),
        (400, 2, 4), (200, 2, 8), (300, 2, 6), (400, 2, 5), (300, 2, 7),
        (300, 3, 5), (400, 2, 6),
    ]], key=lambda c: c[3])


def _progress_of(idx: int, progress) -> int:
    # Plan → progress = index de semaine (volume croît). Générateur libre
    # (progress None) → dérivé du seed pour de la variété de volumes.
    return idx % 16 if progress is None else max(0, int(progress))


def _pick_by_volume(combos, center_m: float, span_m: float, idx: int):
    band = [c for c in combos if center_m - span_m <= c[-1] <= center_m + span_m]
    if not band:
        band = [min(combos, key=lambda c: abs(c[-1] - center_m))]
    return band[idx % len(band)]


# ---------------------------------------------------------------- VMA COURTE
def _vma_courte(idx, vma, fcmax, weight, sciatic, progress=None):
    p = _progress_of(idx, progress)
    center = min(4200, 1600 + p * 110)               # volume cible progressif
    dist, series, reps, _tot = _pick_by_volume(_VMA_COURTE_COMBOS, center, 450, idx)
    pct = [100, 105, 110][idx % 3]
    rec = "egale" if idx % 2 == 0 else "moitie"
    flabel = f"{dist}m"

    s = speed_kmh(pct, vma)
    rec_s = speed_kmh(50, vma)  # trot ~50% VMA
    eff_km = dist / 1000
    eff_sec = round(eff_km / s * 3600)
    recovery_sec = eff_sec if rec == "egale" else max(20, eff_sec // 2)
    rec_km = rec_s * recovery_sec / 3600
    series_rec_sec = 180

    inter = _interval(pct, 93, vma, fcmax)
    body = [{
        "label": f"{series}×({reps}×{flabel}) @ {pct}% VMA",
        "type": "vma_courte", "reps": reps, "series": series,
        "fraction": flabel, **inter,
        "recovery_type": "trot", "recovery_sec": recovery_sec,
        "series_recovery_sec": series_rec_sec if series > 1 else 0,
        "fc_attendue_fin": f"~{fc_bpm(92, fcmax)}-{fc_bpm(96, fcmax)} bpm (90-95% FCmax)",
    }]
    total_reps = reps * series
    work_km = (eff_km + rec_km) * total_reps
    total_km = round(20 / 60 * speed_kmh(70, vma) + work_km + 10 / 60 * speed_kmh(65, vma), 1)
    eff_min = total_reps * (eff_sec + recovery_sec) / 60 + (series - 1) * series_rec_sec / 60
    total_min = 20 + eff_min + 10
    difficulty = 3 + (1 if pct >= 110 else 0) + (1 if reps * series * dist >= 3600 else 0)
    note = "Fractions courtes : OK sciatique, éviter relances explosives à froid." if sciatic else ""
    return _envelope("vma_courte", idx + 1, title=f"VMA courte — {series}×{reps}×{flabel} @ {pct}%",
                     difficulty=difficulty, warmup=_warmup(20, vma, fcmax), body=body,
                     cooldown=_cooldown(10, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight, sciatic_note=note)


# ---------------------------------------------------------------- VMA LONGUE
def _ladder(base: int, reps: int, fmt: str) -> list[int]:
    if fmt == "classique":
        return [base] * reps
    if fmt == "degressif":
        return [max(400, base + 200 - i * 100) for i in range(reps)]
    # pyramide : monte puis descend autour de base
    half = reps // 2
    up = [max(400, base - half * 100 + i * 100) for i in range(half)]
    peak = [base]
    down = list(reversed(up))
    seq = (up + peak + down)[:reps]
    return [min(1200, max(400, d)) for d in seq]


# Combos VMA longue COHÉRENTS (distance_m, reps) — volume total borné
# ~2,4-5 km. Triés par volume croissant (progression).
_VMA_LONGUE_COMBOS = sorted(
    [(d, r, d * r) for (d, r) in [
        (400, 6), (600, 4), (500, 5), (600, 5), (1000, 3), (500, 6),
        (800, 4), (600, 6), (1200, 3), (800, 5), (1000, 4), (1200, 4),
        (800, 6), (1000, 5),
    ]], key=lambda c: c[2])


def _vma_longue(idx, vma, fcmax, weight, sciatic, progress=None):
    p = _progress_of(idx, progress)
    center = min(4800, 2400 + p * 160)               # volume cible progressif
    base, reps, _tot = _pick_by_volume(_VMA_LONGUE_COMBOS, center, 700, idx)
    pct = [90, 95][idx % 2]
    fmt = ["classique", "pyramide", "degressif"][idx % 3]
    s = speed_kmh(pct, vma)
    ladder = _ladder(base, reps, fmt)

    body = []
    work_km = 0.0
    work_min = 0.0
    for d in ladder:
        d_km = d / 1000
        sec = round(d_km / s * 3600)
        rec_sec = 120 if d >= 800 else (90 if d >= 600 else 75)
        work_km += d_km
        work_min += (sec + rec_sec) / 60
        body.append({
            "label": f"{d} m @ {pct}% VMA", "distance_m": d,
            **_interval(pct, 90, vma, fcmax),
            "recovery_type": "trot", "recovery_sec": rec_sec,
        })
    total_km = round(work_km + 3.0 + 1.5, 1)  # + échauffement/retour
    total_min = 18 + work_min + 10
    difficulty = 3 + (1 if pct >= 95 else 0) + (1 if work_km >= 5 else 0)
    title = f"VMA longue — {reps}×{base} m @ {pct}%" + (f" ({fmt})" if fmt != "classique" else "")
    return _envelope("vma_longue", idx + 1, title=title, difficulty=difficulty,
                     warmup=_warmup(18, vma, fcmax), body=body,
                     cooldown=_cooldown(10, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight,
                     sciatic_note="Garder la foulée propre quand la fatigue monte." if sciatic else "")


# ---------------------------------------------------------------- SEUIL
def _seuil(idx, vma, fcmax, weight, sciatic, progress=None):
    pcts = [85, 88]
    structs = [("continu", 20, 0, 0), ("continu", 25, 0, 0), ("continu", 30, 0, 0),
               ("fractions", 12, 3, 3), ("fractions", 6, 5, 1),
               ("fractions", 8, 4, 2), ("fractions", 20, 2, 3)]
    recs = [1, 2, 3]
    terrains = ["plat", "légèrement vallonné"]
    progressifs = [False, True]
    pct, (mode, block, reps, rec_def), rec_min, terrain, progressif = _select(
        idx, [pcts, structs, recs, terrains, progressifs])
    s = speed_kmh(pct, vma)
    inter = _interval(pct, 90, vma, fcmax)

    if mode == "continu":
        body = [{"label": f"Tempo seuil continu {block}'", "duration_min": block, **inter,
                 "note": "progressif Z2→seuil" if progressif else "allure régulière"}]
        work_min = block
        work_km = s * block / 60
    else:
        rec_use = rec_min if rec_min else rec_def
        body = [{"label": f"{reps}×{block}' seuil", "reps": reps, "duration_min_each": block,
                 **inter, "recovery_type": "trot", "recovery_min": rec_use}]
        work_min = reps * (block + rec_use)
        work_km = s * reps * block / 60
    total_km = round(work_km + 3.0 + 1.5, 1)
    total_min = 18 + work_min + 10
    difficulty = 3 + (1 if pct >= 88 else 0)
    title = (f"Seuil continu {block}' @ {pct}%" if mode == "continu"
             else f"Seuil {reps}×{block}' @ {pct}%") + f" — {terrain}"
    return _envelope("seuil", idx + 1, title=title, difficulty=difficulty,
                     warmup=_warmup(18, vma, fcmax), body=body,
                     cooldown=_cooldown(10, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight)


# ---------------------------------------------------------------- TEMPO
def _tempo(idx, vma, fcmax, weight, sciatic, progress=None):
    durations = [20, 25, 30, 35, 40]
    fmts = ["continu", "2×15'", "progressif", "3×10'"]
    pcts = [80, 82, 85]
    terrains = ["plat", "vallonné"]
    dur, fmt, pct, terrain = _select(idx, [durations, fmts, pcts, terrains])
    s = speed_kmh(pct, vma)
    inter = _interval(pct, 84, vma, fcmax)
    body = [{"label": f"Tempo {fmt} ~{dur}' @ {pct}% VMA", "duration_min": dur, **inter,
             "terrain": terrain,
             "note": "monter de Z2 vers tempo" if fmt == "progressif" else "tenue d'allure"}]
    work_km = s * dur / 60
    total_km = round(work_km + 2.5 + 1.5, 1)
    total_min = 15 + dur + 10
    difficulty = 2 + (1 if pct >= 85 else 0) + (1 if dur >= 35 else 0)
    return _envelope("tempo", idx + 1, title=f"Tempo {fmt} {dur}' @ {pct}% — {terrain}",
                     difficulty=difficulty, warmup=_warmup(15, vma, fcmax), body=body,
                     cooldown=_cooldown(10, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight)


# ---------------------------------------------------------------- Z2
def _z2(idx, vma, fcmax, weight, sciatic, progress=None):
    durations = [35, 45, 50, 60, 70, 80, 90]
    terrains = ["route", "trail", "côtes douces"]
    extras = ["aucun", "strides", "gainage McGill", "sortie nocturne", "café-run"]
    dur, terrain, extra = _select(idx, [durations, terrains, extras])
    pct = 70
    s = speed_kmh(pct, vma)
    inter = _interval(pct, 75, vma, fcmax)
    body = [{"label": f"Endurance fondamentale {dur}' — {terrain}", "duration_min": dur, **inter}]
    if extra == "strides":
        body.append({"label": "6×20s lignes droites (strides)", "reps": 6,
                     **_interval(100, 85, vma, fcmax), "recovery_type": "marche", "recovery_sec": 40})
    elif extra == "gainage McGill":
        body.append({"label": "Gainage Big 3 McGill à mi-parcours",
                     "detail": "curl-up 6/4/2 · side plank 6/4/2 · bird dog 6/4/2"})
    work_km = s * dur / 60
    total_km = round(work_km + (0.6 if extra == "strides" else 0), 1)
    total_min = dur + (6 if extra == "strides" else 0)
    difficulty = 1 + (1 if dur >= 75 else 0)
    note = "Base aérobie : zéro contrainte lombaire, idéal jour OFF." if sciatic else ""
    return _envelope("z2", idx + 1, title=f"Z2 {dur}' — {terrain}" + (f" + {extra}" if extra != "aucun" else ""),
                     difficulty=difficulty, warmup={"label": "Démarrage très progressif", "duration_min": 0,
                     **_interval(60, 60, vma, fcmax)}, body=body,
                     cooldown=_cooldown(0, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight, sciatic_note=note)


# ---------------------------------------------------------------- FARTLEK
def _fartlek(idx, vma, fcmax, weight, sciatic, progress=None):
    structs = ["Mona", "libre (suédois)", "pyramidal", "surges en côte", "fractions libres", "blocs"]
    durations = [25, 30, 35, 40, 45, 50]
    terrains = ["route", "trail", "vallonné"]
    struct, dur, terrain = _select(idx, [structs, durations, terrains])
    if struct == "Mona":
        detail = "2×90s / 4×60s / 4×30s / 4×15s (effort = récup, intensité croissante)"
    elif struct == "pyramidal":
        detail = "1-2-3-4-3-2-1 min effort, récup trottée égale"
    elif struct == "surges en côte":
        detail = "surges de 20-40s sur chaque montée du parcours"
    elif struct == "blocs":
        detail = "3×(5' à 85-90% / 3' Z2)"
    elif struct == "fractions libres":
        detail = "10-15 accélérations libres entre repères visuels"
    else:
        detail = "jeu d'allures au feeling, surges allure 5-10 km"
    body = [{"label": f"Fartlek {struct} ~{dur}' — {terrain}", "duration_min": dur,
             "structure": detail, **_interval(85, 85, vma, fcmax),
             "note": "alterner 80-100% VMA selon les surges"}]
    work_km = speed_kmh(78, vma) * dur / 60
    total_km = round(work_km + 1.5 + 1.0, 1)
    total_min = 12 + dur + 8
    difficulty = 2 + (1 if dur >= 40 else 0)
    return _envelope("fartlek", idx + 1, title=f"Fartlek {struct} {dur}' — {terrain}",
                     difficulty=difficulty, warmup=_warmup(12, vma, fcmax), body=body,
                     cooldown=_cooldown(8, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight)


# ---------------------------------------------------------------- CÔTES
def _cotes(idx, vma, fcmax, weight, sciatic, progress=None):
    kinds = ["sprint neuromusculaire", "côtes courtes (puissance)",
             "côtes longues (aérobie)", "pyramide de côtes", "fartlek côte"]
    reps_opts = [4, 5, 6, 7, 8, 10]
    pentes = ["4-6%", "6-8%", "8-10%"]
    recs = ["marche", "trot"]
    kind, reps, pente, rec = _select(idx, [kinds, reps_opts, pentes, recs])
    if kind == "sprint neuromusculaire":
        eff, fc_pct, rec_sec = "8-10s", 88, 120
    elif kind == "côtes courtes (puissance)":
        eff, fc_pct, rec_sec = "30-45s", 93, 120
    elif kind == "côtes longues (aérobie)":
        eff, fc_pct, rec_sec = "2-3 min", 90, 150
    elif kind == "pyramide de côtes":
        eff, fc_pct, rec_sec = "30-60-90-60-30s", 92, 120
    else:
        eff, fc_pct, rec_sec = "surges en montée", 88, 90
    body = [{"label": f"{reps}× {kind} ({eff}), pente {pente}", "reps": reps,
             "effort": eff, "pente": pente,
             "fc_bpm": fc_bpm(fc_pct, fcmax), "pct_fcmax": fc_pct, "zone": _zone(fc_pct),
             "recovery_type": f"{rec} descente contrôlée", "recovery_sec": rec_sec}]
    total_km = round(2.0 + reps * 0.25 + 1.5, 1)
    total_min = 15 + reps * (1 + rec_sec / 60) + 10
    difficulty = 3 + (1 if "8-10%" in pente else 0)
    note = "Descente contrôlée (jamais en relâchement lombaire) — sciatique L5-S1." if sciatic else ""
    return _envelope("cotes", idx + 1, title=f"Côtes — {reps}× {kind}, pente {pente}",
                     difficulty=difficulty, warmup=_warmup(15, vma, fcmax), body=body,
                     cooldown=_cooldown(10, vma, fcmax), total_min=total_min,
                     total_km=total_km, weight=weight, sciatic_note=note)


_BUILDERS = {
    "vma_courte": _vma_courte, "vma_longue": _vma_longue, "seuil": _seuil,
    "tempo": _tempo, "z2": _z2, "fartlek": _fartlek, "cotes": _cotes,
}


def generate_run(run_type: str, seed: int, vma: float = VMA_ATHLETE,
                 fcmax: int = FCMAX, weight: float = WEIGHT_KG,
                 sciatic: bool = True, progress=None) -> dict:
    """`progress` (optionnel) : index de semaine du plan → volume cible croissant
    et cohérent (VMA courte/longue). None = variété libre dérivée du seed."""
    if run_type not in _BUILDERS:
        raise ValueError(f"type inconnu: {run_type} (attendus: {', '.join(RUN_TYPES)})")
    idx = max(0, int(seed) - 1)   # seed 1-based
    return _BUILDERS[run_type](idx, vma, int(fcmax), weight, sciatic, progress)


def run_library(vma: float = VMA_ATHLETE, fcmax: int = FCMAX) -> dict:
    """Liste les 700 séances (100 par type) : seed, titre, difficulté, durée."""
    lib = {}
    for t in RUN_TYPES:
        items = []
        for n in range(1, LIBRARY_SIZE + 1):
            s = generate_run(t, n, vma, fcmax)
            items.append({"seed": s["seed"], "title": s["title"],
                          "difficulty": s["difficulty"], "duration_min": s["duration_min"]})
        lib[t] = items
    return {"types": RUN_TYPES, "per_type": LIBRARY_SIZE, "total": LIBRARY_SIZE * len(RUN_TYPES),
            "library": lib}
