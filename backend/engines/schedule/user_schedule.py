"""Rythme de travail PAR ATHLÈTE — config-driven (multi-utilisateurs).

Deux types de rythme :
- 'police_3223' : 3/2/2/3, avec ancre propre à l'athlète (→ phase identique ou
  opposée au propriétaire). Service = séance courte, OFF = double séance.
- 'weekly'      : l'athlète choisit ses jours d'entraînement ; les autres jours
  sont du repos. Rotation équilibrée force/course/WOD répartie sur ces jours.

La config est stockée dans athlete_profiles.work_schedule (JSON). Tout le
moteur de plan (weekly_plan, standby) et l'agenda passent par cette couche.
"""
from __future__ import annotations

from datetime import date, timedelta

from . import police_schedule as P

DAY_CODES = P.DAY_CODES
_DEFAULT_WEEKLY = ["mon", "wed", "fri", "sun"]


def normalize(work_schedule: dict | None) -> dict:
    """Config normalisée. Défaut = 3/2/2/3 ancre propriétaire (rétro-compatible).
    `training_style` : 'split' (push/pull/legs, défaut) ou 'fullbody'.
    `start_monday` (weekly) / `anchor_big_week_monday` (police) = J0 du programme
    → la progression 5/3/1 démarre à cette date (cycle 0)."""
    ws = work_schedule or {}
    style = "fullbody" if ws.get("training_style") == "fullbody" else "split"
    if ws.get("type") == "weekly":
        days = [d for d in (ws.get("training_days") or []) if d in DAY_CODES]
        out = {"type": "weekly", "training_days": days or _DEFAULT_WEEKLY,
               "training_style": style}
        if ws.get("start_monday"):
            out["start_monday"] = ws["start_monday"]
        return out
    anchor = ws.get("anchor_big_week_monday") or P.ANCHOR_MONDAY.isoformat()
    out = {"type": "police_3223", "anchor_big_week_monday": anchor,
           "training_style": style}
    # `start_monday` est conservé AUSSI en police : il découple le J0 de la
    # progression 5/3/1 de l'ancre du rythme de travail. Sans lui, recaler la
    # phase (« cette semaine est ma petite semaine ») décalerait le cycle de
    # force d'une semaine — ce qui n'a rien à voir avec le planning de service.
    if ws.get("start_monday"):
        out["start_monday"] = ws["start_monday"]
    return out


def plan_start(config: dict) -> date:
    """J0 du programme (la progression 5/3/1 démarre ici).
    `start_monday` explicite s'il existe (les deux rythmes) ; sinon police =
    l'ancre (lundi de grande semaine), weekly = ancre globale."""
    sm = config.get("start_monday")
    if sm:
        try:
            return date.fromisoformat(sm)
        except (ValueError, TypeError):
            pass
    if config.get("type") == "weekly":
        return P.ANCHOR_MONDAY
    return _anchor(config)


def anchor_for_current_week(is_big: bool, today: date | None = None) -> str:
    """Convertit « cette semaine est grande/petite » en date d'ancre (lundi).
    Ancre = un lundi de GRANDE semaine."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    # si la semaine en cours est petite, l'ancre (grande) est la semaine d'avant
    return (monday if is_big else monday - timedelta(days=7)).isoformat()


def _anchor(config: dict) -> date:
    return date.fromisoformat(config["anchor_big_week_monday"])


def week_type_for(config: dict, d: date) -> str:
    if config["type"] == "weekly":
        return "weekly"
    return P.week_type_for(d, _anchor(config))


def is_work_day(config: dict, d: date) -> bool:
    # Police : jour de service. Weekly : pas de notion de service → False.
    if config["type"] == "weekly":
        return False
    return P.is_work_day(d, _anchor(config))


def day_schedule(config: dict, d: date) -> dict:
    """Infos jour pour l'UI/agenda, selon le rythme de l'athlète."""
    code = DAY_CODES[d.weekday()]
    if config["type"] == "weekly":
        trains = code in config["training_days"]
        return {
            "date": d.isoformat(), "day_of_week": code, "week_type": "weekly",
            "is_work_day": False, "trains": trains,
            "training_slot": "training" if trains else "rest",
            "intent": {"focus": "single" if trains else "rest",
                       "label": "Séance du jour" if trains else "Repos",
                       "load": "moderate" if trains else "light"},
        }
    ds = P.day_schedule(d, _anchor(config)).to_dict()
    ds["trains"] = True
    return ds


def week_schedule(config: dict, d: date) -> dict:
    monday = d - timedelta(days=d.weekday())
    days = [day_schedule(config, monday + timedelta(days=i)) for i in range(7)]
    if config["type"] == "weekly":
        work = sorted([c for c in DAY_CODES if c in config["training_days"]])
        return {"monday": monday.isoformat(), "week_type": "weekly",
                "work_days": work,
                "off_days": [c for c in DAY_CODES if c not in config["training_days"]],
                "days": days}
    return P.week_schedule(monday, _anchor(config))


# ---- Templates d'entraînement (specs de séances par jour de semaine) ----
# Rotation hebdo équilibrée pour le mode weekly (force/course/WOD, anti-lombaire).
_WEEKLY_ROTATION = [
    ("strength", "push"), ("run", "seuil"), ("strength", "pull"),
    ("run", "vma_courte"), ("strength", "legs"), ("crossfit", None), ("run", "z2"),
]


def week_template(config: dict, plan_w: int, week_type: str,
                  big_template: dict, small_template: dict) -> dict[int, list]:
    """Renvoie {weekday(0..6): [specs]} pour la semaine.
    - police : templates 3/2/2/3 fournis (big/small) selon le type de semaine.
    - weekly : rotation équilibrée répartie sur les jours d'entraînement choisis,
      décalée par `plan_w` pour varier d'une semaine à l'autre."""
    if config["type"] != "weekly":
        return big_template if week_type == P.BIG_WORK else small_template
    chosen = [i for i in range(7) if DAY_CODES[i] in config["training_days"]]
    template: dict[int, list] = {i: [] for i in range(7)}
    start = plan_w % len(_WEEKLY_ROTATION)
    for n, wd in enumerate(chosen):
        disc, sub = _WEEKLY_ROTATION[(start + n) % len(_WEEKLY_ROTATION)]
        template[wd] = [("matin", disc, sub)]
    return template
