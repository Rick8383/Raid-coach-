"""Générateur de WOD CrossFit — 15 formats, variété garantie, déterministe par seed.

Règles de cohérence : distances run/carry FIXES, équilibre push/pull/legs/cardio,
charges de conditioning (~70-80%, pas de 1RM), et règle sciatique L5-S1
(mouvements lombaires exclus si exclude_lumbar, jamais en dernière position d'un
WOD long).
"""
from __future__ import annotations

import hashlib
import random

from .movements import CARDIO_MACHINES, pool as _pool

WOD_FORMATS = [
    "amrap", "for_time", "emom", "death_by", "death_by_emom", "chipper",
    "buy_in_amrap_buy_out", "pyramid_asc", "pyramid_desc", "pyramid_full",
    "multi_amrap_blocks", "rft", "tabata", "amrap_score_double", "ladder",
]

_PREFIX = ["OPÉRATION", "PROTOCOLE", "ASSAUT", "SECTEUR", "CODE", "MISSION"]
_NAME = ["VIPÈRE", "FANTÔME", "ORAGE", "GRANIT", "TONNERRE", "CHACAL", "MISTRAL",
         "TITANE", "BRASIER", "ACIER", "CORBEAU", "SOMBRE", "OBSIDIENNE", "FAUCON"]

_MUSCLES = {"push": "pecs/épaules/triceps", "pull": "dos/biceps/grip",
            "legs": "quadriceps/fessiers", "core": "gainage/abdos",
            "cardio": "cardio", "condi": "conditioning"}


def _rng(seed: str) -> random.Random:
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return random.Random(h)


def _name(rng: random.Random) -> str:
    return f"{rng.choice(_PREFIX)} {rng.choice(_NAME)}"


# Reps cohérentes par bande de mouvement (plus de "8 double-unders" absurde)
_BAND_REPS = {"high": [20, 30, 40, 50], "med": [8, 10, 12, 15], "low": [3, 5, 6, 8]}
_BAND_CHIPPER = {"high": [40, 50, 75, 100], "med": [20, 25, 30], "low": [10, 12, 15]}


def _mag(rng: random.Random, move: dict, chipper: bool = False) -> int:
    u = move["unit"]
    if u == "cal":
        return rng.choice([10, 12, 15, 20, 25])
    if u == "m_cardio":
        return rng.choice([250, 500, 1000])
    if u == "m_run":
        return rng.choice([100, 200, 400])
    if u == "m_carry":
        return rng.choice([20, 30, 50])
    band = move.get("band", "med")
    return rng.choice((_BAND_CHIPPER if chipper else _BAND_REPS)[band])


def _render(move: dict, mag) -> str:
    u, name = move["unit"], move["name"]
    load = f" @{move['load']}kg" if move.get("load") else ""
    if u == "cal":
        return f"{mag} {name}"
    if u in ("m_cardio", "m_run"):
        return f"{mag} m {name}"
    if u == "m_carry":
        return f"{mag} m {name}{load}"
    if u == "s":
        return f"{mag}s {name}"
    return f"{mag} {name}{load}"


def _pick(rng: random.Random, moves: list[dict], k: int, need_cardio: bool = True) -> list[dict]:
    """k mouvements distincts, variété de patterns, au moins un cardio si demandé."""
    avail = moves[:]
    rng.shuffle(avail)
    chosen: list[dict] = []
    if need_cardio:
        cardio = [m for m in avail if m["pattern"] == "cardio"]
        # privilégier une machine (assault/echo/ski/row) à la course pure
        machines = [m for m in cardio if m["id"] in CARDIO_MACHINES]
        if machines and rng.random() < 0.8:
            chosen.append(rng.choice(machines))
        elif cardio:
            chosen.append(cardio[0])
    seen_patterns = {m["pattern"] for m in chosen}
    # privilégier des patterns variés
    for m in avail:
        if len(chosen) >= k:
            break
        if m in chosen:
            continue
        if m["pattern"] in seen_patterns and len([x for x in avail if x["pattern"] not in seen_patterns and x not in chosen]) > 0:
            continue
        chosen.append(m)
        seen_patterns.add(m["pattern"])
    for m in avail:  # compléter si pas assez
        if len(chosen) >= k:
            break
        if m not in chosen:
            chosen.append(m)
    return chosen[:k]


def _reps_move(rng, moves, k):
    """k mouvements à reps pour les schémas 21-15-9 (bandes med/low, pas de
    mouvement haut-volume type double-unders sur ces schémas)."""
    rep_pool = [m for m in moves if m["unit"] == "reps" and m.get("band") != "high"]
    rng.shuffle(rep_pool)
    out, pats = [], set()
    for m in rep_pool:
        if len(out) >= k:
            break
        if m["pattern"] in pats and len(out) < k:
            continue
        out.append(m)
        pats.add(m["pattern"])
    for m in rep_pool:
        if len(out) >= k:
            break
        if m not in out:
            out.append(m)
    return out[:k]


def _muscles(moves: list[dict]) -> str:
    pats = []
    for m in moves:
        lbl = _MUSCLES.get(m["pattern"], "")
        if lbl and lbl not in pats:
            pats.append(lbl)
    return " · ".join(pats)


def _lumbar_note(moves: list[dict], exclude_lumbar: bool) -> str:
    if any(m["lumbar"] for m in moves):
        return "caution — contient un mouvement lombaire, garder le dos neutre"
    return "safe — aucun mouvement à risque lombaire (compatible sciatique L5-S1)"


# ---------------- Format builders -> (lines, label, cap_or_dur, score, diff) ----------------
def _b_amrap(rng, dur, pool):
    k = 2 if dur < 10 else rng.choice([3, 4])
    moves = _pick(rng, pool, k)
    lines = [_render(m, _mag(rng, m)) for m in moves]
    return lines, f"AMRAP {dur} min", f"{dur} min", "Viser le maximum de tours", moves

def _b_for_time(rng, dur, pool):
    scheme = rng.choice([[21, 15, 9], [10, 8, 6], [50, 40, 30]])
    moves = _reps_move(rng, pool, 2)
    sched = "-".join(str(x) for x in scheme)
    lines = [f"{sched} reps : " + " / ".join(m["name"] + (f" @{m['load']}kg" if m.get("load") else "") for m in moves)]
    cap = rng.choice([8, 10, 12, 15])
    return lines, "For Time", f"time cap {cap} min", "Le plus rapide possible", moves

def _b_emom(rng, dur, pool):
    moves = _pick(rng, pool, rng.choice([2, 3]), need_cardio=True)
    lines = [f"Min {i + 1} : " + _render(m, min(6, _mag(rng, m)) if m["unit"] == "reps" else _mag(rng, m))
             for i, m in enumerate(moves)]
    lines.append("→ alterner ces minutes jusqu'à la fin (≥15s de repos/min)")
    return lines, f"EMOM {dur} min", f"{dur} min", "Tenir la qualité chaque minute", moves

def _b_death_by(rng, dur, pool):
    m = _pick(rng, pool, 1, need_cardio=False)[0]
    lines = [f"Min 1 : 1 {m['name']}, +1 rep chaque minute jusqu'à l'échec"]
    return lines, "Death by", "jusqu'à échec", "Aller le plus loin possible", [m]

def _b_death_by_emom(rng, dur, pool):
    moves = _pick(rng, pool, 2, need_cardio=True)
    lines = [f"+1 rep/min de chaque : " + " + ".join(m["name"] for m in moves),
             "Min N = N reps de chaque mouvement, jusqu'à l'échec"]
    return lines, "Death by EMOM", "jusqu'à échec", "Dernière minute complétée", moves

def _b_chipper(rng, dur, pool):
    moves = _pick(rng, pool, rng.choice([5, 6, 7]), need_cardio=True)
    lines = [_render(m, _mag(rng, m, chipper=True)) for m in moves]
    return lines, "Chipper (1 tour)", f"time cap {rng.choice([16,18,20])} min", "Finir la liste", moves

def _b_buy_in(rng, dur, pool):
    cardio = [m for m in pool if m["pattern"] == "cardio"]
    rng.shuffle(cardio)
    buyin, buyout = cardio[0], cardio[1] if len(cardio) > 1 else cardio[0]
    mid = _pick(rng, [m for m in pool if m["pattern"] != "cardio"], 2, need_cardio=False)
    lines = [f"Buy-in : {_render(buyin, rng.choice([400,500]) if buyin['unit'] in ('m_cardio','m_run') else 20)}",
             f"Puis AMRAP {dur - 4} min : " + " / ".join(_render(m, _mag(rng, m)) for m in mid),
             f"Buy-out : {_render(buyout, rng.choice([400,500]) if buyout['unit'] in ('m_cardio','m_run') else 20)}"]
    return lines, "Buy-in + AMRAP + Buy-out", f"{dur} min", "Max de tours sur le bloc central", [buyin] + mid + [buyout]

def _b_pyr_asc(rng, dur, pool):
    moves = _reps_move(rng, pool, 2)
    lines = ["Échelle 1-2-3-4-5-6-7-8-9-10 reps de : " + " + ".join(m["name"] + (f" @{m['load']}kg" if m.get('load') else "") for m in moves)]
    return lines, "Pyramide ascendante", f"time cap {rng.choice([12,15])} min", "Monter le plus haut", moves

def _b_pyr_desc(rng, dur, pool):
    moves = _reps_move(rng, pool, 2)
    lines = ["Échelle 10-9-8-7-6-5-4-3-2-1 reps de : " + " + ".join(m["name"] for m in moves)]
    return lines, "Pyramide descendante", f"time cap {rng.choice([12,15])} min", "Le plus rapide", moves

def _b_pyr_full(rng, dur, pool):
    moves = _reps_move(rng, pool, 2)
    sched = rng.choice(["1-2-3-4-5-4-3-2-1", "3-6-9-12-9-6-3"])
    lines = [f"Pyramide {sched} reps de : " + " + ".join(m["name"] for m in moves)]
    return lines, "Pyramide complète", f"time cap {rng.choice([14,16,18])} min", "Finir la pyramide", moves

def _b_multi_amrap(rng, dur, pool):
    blocks = rng.choice([2, 3])
    lines = []
    moves_all = []
    for b in range(blocks):
        mv = _pick(rng, pool, 2)
        moves_all += mv
        lines.append(f"Bloc {b + 1} — AMRAP 5 min : " + " / ".join(_render(m, _mag(rng, m)) for m in mv))
    lines.append("Repos 2 min entre les blocs")
    return lines, f"{blocks}×(5 min AMRAP)", f"{blocks * 5 + (blocks - 1) * 2} min", "Score = total des tours", moves_all

def _b_rft(rng, dur, pool):
    rounds = rng.choice([3, 4, 5])
    moves = _pick(rng, pool, 3, need_cardio=True)
    lines = [f"{rounds} tours pour le temps :"] + [_render(m, _mag(rng, m)) for m in moves]
    return lines, f"{rounds} RFT", f"time cap {rounds * 5} min", "Le plus rapide", moves

def _b_tabata(rng, dur, pool):
    moves = _pick(rng, pool, rng.choice([1, 2, 3]), need_cardio=False)
    lines = ["8×(20s travail / 10s repos) — score = reps du tour le plus faible :"] + [m["name"] for m in moves]
    return lines, "Tabata", "4 min/mouvement", "Maximiser le tour le plus faible", moves

def _b_amrap_double(rng, dur, pool):
    lines, _, _, _, moves = _b_amrap(rng, dur, pool)
    return lines, f"AMRAP {dur} min (score ×2)", f"{dur} min", "Score doublé (format compétition)", moves

def _b_ladder(rng, dur, pool):
    rep_moves = _reps_move(rng, pool, 1)
    fixed = _pick(rng, [m for m in pool if m not in rep_moves], 1, need_cardio=False)[0]
    lines = [f"Montée 3-6-9-12-15 {rep_moves[0]['name']}",
             f"+ {_render(fixed, _mag(rng, fixed))} fixe à chaque tour"]
    return lines, "Ladder", f"time cap {rng.choice([10,12])} min", "Monter l'échelle", rep_moves + [fixed]


_BUILDERS = {
    "amrap": _b_amrap, "for_time": _b_for_time, "emom": _b_emom,
    "death_by": _b_death_by, "death_by_emom": _b_death_by_emom, "chipper": _b_chipper,
    "buy_in_amrap_buy_out": _b_buy_in, "pyramid_asc": _b_pyr_asc,
    "pyramid_desc": _b_pyr_desc, "pyramid_full": _b_pyr_full,
    "multi_amrap_blocks": _b_multi_amrap, "rft": _b_rft, "tabata": _b_tabata,
    "amrap_score_double": _b_amrap_double, "ladder": _b_ladder,
}


def generate_wod(fmt: str = "auto", duration_min: int = 12, seed: str = "wod",
                 exclude_lumbar: bool = True, bodyweight: bool = False) -> dict:
    rng = _rng(f"{fmt}:{duration_min}:{seed}:{exclude_lumbar}:{bodyweight}")
    if fmt == "auto" or fmt not in _BUILDERS:
        fmt = rng.choice(WOD_FORMATS)
    dur = max(4, min(int(duration_min), 30))
    pool = _pool(exclude_lumbar, bodyweight)
    lines, label, cap, score, moves = _BUILDERS[fmt](rng, dur, pool)

    # Règle WOD long : aucun mouvement lombaire en dernière position
    if not exclude_lumbar and dur > 15 and moves and moves[-1].get("lumbar"):
        safe = [m for m in moves if not m["lumbar"]]
        if safe:
            lines.append("⚠ placer le mouvement lombaire en début/milieu, jamais en finisseur")

    has_lumbar = any(m["lumbar"] for m in moves)
    difficulty = 2 + (1 if dur >= 15 else 0) + (1 if any(m.get("load") for m in moves) else 0) \
        + (1 if len(moves) >= 5 else 0)
    return {
        "name": _name(rng),
        "format": label,
        "format_key": fmt,
        "duration_or_cap": cap,
        "description": lines,
        "target_score": score,
        "muscles": _muscles(moves),
        "difficulty": max(1, min(5, difficulty)),
        "lumbar_note": _lumbar_note(moves, exclude_lumbar),
        "lumbar_safe": not has_lumbar,
        "seed": seed,
        "exclude_lumbar": exclude_lumbar,
        "bodyweight": bodyweight,
    }


def random_wod(exclude_lumbar: bool = True) -> dict:
    seed = hashlib.sha256(random.SystemRandom().randbytes(16)).hexdigest()[:12]
    fmt = random.SystemRandom().choice(WOD_FORMATS)
    dur = random.SystemRandom().choice([8, 10, 12, 15, 18, 20])
    return generate_wod(fmt, dur, seed, exclude_lumbar)
