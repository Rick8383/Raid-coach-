"""Plan glissant détaillé (Mission 1B) — N semaines jour par jour.

Assemble, pour chaque jour, les séances réelles via les générateurs :
- course (Mission 2), force 5/3/1 (Mission 4), WOD (Mission 3), natation/récup.
Respecte le planning police 3/2/2/3 (jour OFF = double séance possible, jour de
service = séance unique courte, dimanche petite semaine = natation récup).

Le 5/3/1 progresse avec le calendrier : semaine_dans_cycle = (W % 4) + 1,
cycle = W // 4 (W = index de semaine absolu depuis l'ancre 2026-06-15).
"""
from __future__ import annotations

from datetime import date, timedelta

from engines import schedule as _sched
from engines.schedule import user_schedule as _us
from engines.run_generator import generate_run
from engines.strength_531 import generate_strength_531
from engines.wod_generator import generate_wod

START = date(2026, 6, 15)   # ancre lundi, grande semaine

# Templates hebdo : weekday (0=lun..6=dim) -> liste de specs séance.
# spec = (moment, type, sous-type)  ; sous-type = run_type ou jour force.
_BIG_WORK = {   # service lun/mar/ven/sam/dim ; OFF mer/jeu
    0: [("matin", "strength", "push")],                       # lun (service, court)
    1: [("matin", "run", "tempo")],                           # mar (service)
    2: [("matin", "run", "vma_courte"), ("soir", "strength", "pull")],   # mer OFF
    3: [("matin", "run", "z2"), ("soir", "crossfit", None)],  # jeu OFF
    4: [("matin", "strength", "legs")],                       # ven (service)
    5: [("matin", "run", "seuil")],                           # sam (service)
    6: [("matin", "crossfit", None)],                         # dim (service, WOD court)
}
_SMALL_WORK = {  # service mer/jeu ; OFF le reste
    0: [("matin", "run", "vma_courte"), ("soir", "strength", "push")],   # lun OFF
    1: [("matin", "run", "cotes"), ("soir", "strength", "pull")],        # mar OFF
    2: [("matin", "run", "tempo")],                           # mer (service)
    3: [("matin", "strength", "legs")],                       # jeu (service)
    4: [("matin", "run", "vma_longue"), ("soir", "crossfit", None)],     # ven OFF
    5: [("matin", "run", "z2"), ("soir", "crossfit", None)],  # sam OFF
    6: [("matin", "swim", None)],                             # dim OFF (récup)
}


def _swim_session() -> dict:
    return {"title": "Natation récupération + apnée", "duration_min": 40,
            "detail": {"blocks": ["200m échauffement souple",
                                  "6×50m crawl aérobie (récup 20s)",
                                  "4×25m apnée progressive (jamais forcer)",
                                  "100m retour au calme"]}}


def _build_session(spec, w_index, weekday, vma, fcmax):
    moment, stype, sub = spec
    if stype == "run":
        seed = ((w_index * 3 + weekday) % 100) + 1
        detail = generate_run(sub, seed, vma, fcmax)
        dur = detail["duration_min"]
        title = detail["title"]
    elif stype == "strength":
        week_in_cycle = (w_index % 4) + 1
        cycle = w_index // 4
        detail = generate_strength_531(sub, week_in_cycle, cycle)
        dur = 70 if week_in_cycle != 4 else 55
        title = f"Force {sub.upper()} — S{week_in_cycle}" + (" deload" if week_in_cycle == 4 else "")
    elif stype == "crossfit":
        detail = generate_wod("auto", 14, f"plan_{w_index}_{weekday}", exclude_lumbar=True)
        dur = 35
        title = detail["name"]
    else:  # swim
        sw = _swim_session()
        return {"moment": moment, "type": "swim", "title": sw["title"],
                "duration_min": sw["duration_min"], "detail": sw["detail"]}
    return {"moment": moment, "type": stype, "title": title, "duration_min": dur, "detail": detail}


def _day_payload(d: date, shift_weeks: int, vma: float, fcmax: int,
                 config: dict | None = None) -> dict:
    # La STRUCTURE (jours d'entraînement, type de semaine) suit le RYTHME de
    # l'athlète (config) calé sur le calendrier réel ; seule la PROGRESSION
    # (cycle 5/3/1, seeds) peut être décalée (shift_weeks) — mode standby.
    cfg = _us.normalize(config)
    real_monday = d - timedelta(days=d.weekday())
    ds = _us.day_schedule(cfg, d)
    wt = ds["week_type"]
    real_w = max(0, (real_monday - START).days // 7)
    plan_w = max(0, real_w - max(0, int(shift_weeks)))
    template = _us.week_template(cfg, plan_w, wt, _BIG_WORK, _SMALL_WORK)
    sessions = [_build_session(spec, plan_w, d.weekday(), vma, fcmax)
                for spec in template[d.weekday()]]
    return {
        "date": d.isoformat(),
        "day_of_week": ds["day_of_week"],
        "is_work_day": ds["is_work_day"],
        "week_type": wt,
        "week_index": plan_w,
        "sessions": sessions,
    }


def build_day(d: date, vma: float = 14.0, fcmax: int = 186, shift_weeks: int = 0,
              config: dict | None = None) -> dict:
    """Séances planifiées pour une date — MÊME source que build_weekly (mêmes
    seeds), calées sur le RYTHME de l'athlète (config). `shift_weeks` décale la
    progression (standby) sans toucher au calendrier."""
    return _day_payload(d, shift_weeks, vma, fcmax, config)


def build_weekly(from_week: int = 0, n: int = 6, vma: float = 14.0, fcmax: int = 186,
                 config: dict | None = None) -> dict:
    from_week = max(0, min(int(from_week), 200))
    n = max(1, min(int(n), 12))
    weeks = []
    for offset in range(n):
        w_index = from_week + offset
        monday = START + timedelta(weeks=w_index)
        days = [_day_payload(monday + timedelta(days=wd), 0, vma, fcmax, config)
                for wd in range(7)]
        weeks.append({"week_index": w_index, "monday": monday.isoformat(),
                      "week_type": days[0]["week_type"], "days": days})
    return {"from_week": from_week, "n": n, "weeks": weeks}
