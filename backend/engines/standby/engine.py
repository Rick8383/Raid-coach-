"""Mode standby / vacances — adapte le plan quand l'athlète s'absente.

Deux modes, par athlète (isolation totale entre utilisateurs) :
- 'pause'    : pas de salle / pas le temps → plan gelé pendant l'absence, puis
               au retour une semaine de reprise progressive (deload) AVANT de
               reprendre le plan exactement là où il s'était arrêté (le plan est
               « décalé » → aucun cycle 5/3/1 perdu).
- 'vacation' : plus de temps → bloc d'entraînement intensif (salle complète),
               1 ou 2 séances/jour, orienté RAID, cohérent et anti-lombaire.

Logique pure (testable) ; l'état est persisté côté API (StandbyRepository).
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from engines import schedule as _sched
from engines.run_generator import generate_run
from engines.strength_531 import generate_strength_531
from engines.weekly_plan import START as _START, build_day as _build_day
from engines.wod_generator import generate_wod

_REBOOT_DAYS = 7  # durée de la semaine de reprise après une pause


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _real_week(d: date) -> int:
    return max(0, (_monday(d) - _START).days // 7)


def _pause_weeks(start: date, end: date) -> int:
    """Nombre de semaines (calendaires) couvertes par l'absence."""
    return ((_monday(end) - _monday(start)).days // 7) + 1


def _params(state: dict) -> dict:
    raw = state.get("params_json")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return {}
    return {}


# --------------------------------------------------------------------------
# Pliage paresseux : une fois la pause + sa semaine de reprise passées, on
# fige le décalage dans plan_shift_weeks et on efface la fenêtre. Idempotent.
# --------------------------------------------------------------------------
def fold_if_complete(state: dict | None, today: date) -> tuple[dict, bool]:
    base = int((state or {}).get("plan_shift_weeks") or 0)
    cleared = {"mode": None, "start_date": None, "end_date": None,
               "params_json": None, "plan_shift_weeks": base}
    if not state or not state.get("mode"):
        return ({**cleared, "plan_shift_weeks": base}, False)
    mode = state["mode"]
    end = _d(state["end_date"])
    if mode == "pause":
        if today > end + timedelta(days=_REBOOT_DAYS):
            shift = base + _pause_weeks(_d(state["start_date"]), end) + 1
            return ({**cleared, "plan_shift_weeks": shift}, True)
    elif mode == "vacation":
        if today > end:
            return ({**cleared, "plan_shift_weeks": base}, True)
    return (state, False)


def classify_day(d: date, state: dict) -> dict:
    """Détermine ce qu'il faut afficher pour la date `d`."""
    base = int((state or {}).get("plan_shift_weeks") or 0)
    mode = (state or {}).get("mode") or None
    if not mode:
        return {"kind": "normal", "shift": base}
    start, end = _d(state["start_date"]), _d(state["end_date"])
    if mode == "vacation":
        if start <= d <= end:
            return {"kind": "vacation", "index": (d - start).days}
        return {"kind": "normal", "shift": base}
    # pause
    if d < start:
        return {"kind": "normal", "shift": base}
    if start <= d <= end:
        return {"kind": "pause"}
    if end < d <= end + timedelta(days=_REBOOT_DAYS):
        return {"kind": "reboot"}
    return {"kind": "normal", "shift": base + _pause_weeks(start, end) + 1}


# --------------------------------------------------------------------------
# Constructeurs de séances (réutilisent les générateurs réels)
# --------------------------------------------------------------------------
def _seed(d: date, k: int) -> int:
    return (d.toordinal() * 7 + k) % 100 + 1


def _run(sub: str, seed: int, vma: float, fcmax: int, moment: str = "matin") -> dict:
    det = generate_run(sub, seed, vma, fcmax)
    return {"moment": moment, "type": "run", "title": det["title"],
            "duration_min": det["duration_min"], "detail": det}


def _strength(sub: str, week_in_cycle: int, cycle: int, moment: str = "matin") -> dict:
    det = generate_strength_531(sub, week_in_cycle, cycle)
    dur = 70 if week_in_cycle != 4 else 55
    title = f"Force {sub.upper()} — S{week_in_cycle}" + (" deload" if week_in_cycle == 4 else "")
    return {"moment": moment, "type": "strength", "title": title,
            "duration_min": dur, "detail": det}


def _wod(seed: str, dur: int, moment: str = "matin") -> dict:
    det = generate_wod("auto", dur, seed, exclude_lumbar=True)
    return {"moment": moment, "type": "crossfit", "title": det["name"],
            "duration_min": dur, "detail": det}


def _swim(moment: str = "matin") -> dict:
    return {"moment": moment, "type": "swim", "title": "Natation récupération + apnée",
            "duration_min": 40, "detail": {"blocks": [
                "200m échauffement souple", "6×50m crawl aérobie (récup 20s)",
                "4×25m apnée progressive (jamais forcer)", "100m retour au calme"]}}


def _wrap(d: date, sessions: list, kind: str, message: str) -> dict:
    ds = _sched.day_schedule(d)
    return {
        "date": d.isoformat(),
        "day_of_week": ds.day_of_week,
        "is_work_day": ds.is_work_day,
        "week_type": ds.week_type,
        "sessions": sessions,
        "standby": {"mode": kind, "message": message},
    }


def _reboot_sessions(d: date, state: dict, vma: float, fcmax: int) -> list:
    """Semaine de reprise (deload) : volume/intensité réduits, anti-lombaire."""
    ds = _sched.day_schedule(d)
    base = int(state.get("plan_shift_weeks") or 0)
    start, end = _d(state["start_date"]), _d(state["end_date"])
    plan_w = max(0, _real_week(d) - base - _pause_weeks(start, end) - 1)
    cycle = plan_w // 4
    if not ds.is_work_day and ds.day_of_week == "sun" and ds.week_type == _sched.SMALL_WORK:
        return [_swim()]
    if ds.is_work_day:
        return [_run("z2", _seed(d, 1), vma, fcmax)]
    sub = ("push", "pull", "legs")[(_real_week(d) + d.weekday()) % 3]
    return [_run("z2", _seed(d, 1), vma, fcmax, "matin"),
            _strength(sub, 4, cycle, "soir")]  # semaine 4 = deload


def _camp_sessions(d: date, state: dict, index: int, vma: float, fcmax: int) -> list:
    """Bloc vacances (salle complète) : rotation 6 jours orientée RAID."""
    p = _params(state)
    spd = 2 if int(p.get("sessions_per_day") or 1) >= 2 else 1
    start = _d(state["start_date"])
    base = int(state.get("plan_shift_weeks") or 0)
    plan_w = max(0, _real_week(start) - base)
    cycle, wic = plan_w // 4, (plan_w % 4) + 1
    if wic == 4:  # pas de deload en stage intensif
        wic = 3
    i = index % 6
    s = f"camp_{start.isoformat()}_{index}"
    am = {
        0: _strength("push", wic, cycle),
        1: _run("seuil", _seed(d, 2), vma, fcmax),
        2: _strength("pull", wic, cycle),
        3: _run("vma_courte", _seed(d, 3), vma, fcmax),
        4: _strength("legs", wic, cycle),
        5: _wod(s, 16),
    }[i]
    sessions = [am]
    if spd == 2:
        pm = {
            0: _run("z2", _seed(d, 4), vma, fcmax, "soir"),
            1: _wod(s + "b", 10, "soir"),
            2: _run("z2", _seed(d, 5), vma, fcmax, "soir"),
            3: _wod(s + "b", 10, "soir"),
            4: _run("z2", _seed(d, 6), vma, fcmax, "soir"),
            5: _run("z2", _seed(d, 7), vma, fcmax, "soir"),
        }[i]
        sessions.append(pm)
    return sessions


def planned_day(date_iso: str, state: dict, vma: float = 14.0, fcmax: int = 186) -> dict:
    """Séance(s) du jour en tenant compte du mode standby. Même contrat que
    weekly_plan.build_day, plus un champ `standby`."""
    d = _d(date_iso)
    c = classify_day(d, state or {})
    if c["kind"] == "pause":
        return _wrap(d, [], "pause",
                     "Standby — récupération. Au retour : une semaine de reprise "
                     "progressive, puis le plan reprend là où il s'était arrêté.")
    if c["kind"] == "reboot":
        return _wrap(d, _reboot_sessions(d, state, vma, fcmax), "reboot",
                     "Semaine de reprise (deload) après ta coupure — charges et "
                     "volume réduits pour relancer en douceur (sciatique préservée).")
    if c["kind"] == "vacation":
        return _wrap(d, _camp_sessions(d, state, c["index"], vma, fcmax), "vacation",
                     "Mode vacances — bloc intensif salle complète, orienté RAID.")
    payload = _build_day(d, vma, fcmax, shift_weeks=c["shift"])
    payload["standby"] = None
    return payload
