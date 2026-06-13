"""Planning professionnel police — rythme 3/2/2/3.

Source de vérité unique du calendrier de travail. Les semaines alternent :
- GRANDE semaine (big_work)  : service lun/mar/ven/sam/dim → OFF mer/jeu
- PETITE semaine (small_work) : service mer/jeu            → OFF le reste

Ancre calée sur la réalité de l'athlète (verrouillé le 13/06/2026) :
la semaine du lundi 15/06/2026 est une GRANDE semaine.

Côté entraînement (cf. DailyDecisionEngine) : un jour OFF = double séance
possible, un jour de service = séance unique courte, intensité plafonnée.
Le miroir TypeScript de l'app (mobile/src/schedule.ts) doit garder la même
ancre et les mêmes ensembles de jours.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# Ancre : lundi 15/06/2026 = GRANDE semaine. Les semaines alternent ensuite.
ANCHOR_MONDAY = date(2026, 6, 15)

DAY_CODES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

BIG_WORK = "big_work"
SMALL_WORK = "small_work"

# Jours de service (police) selon le type de semaine
_BIG_WORK_DAYS = frozenset({"mon", "tue", "fri", "sat", "sun"})
_SMALL_WORK_DAYS = frozenset({"wed", "thu"})


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def week_type_for(d: date) -> str:
    """big_work / small_work pour la semaine contenant `d`."""
    weeks = (_monday_of(d) - ANCHOR_MONDAY).days // 7
    # Python : le modulo d'un négatif reste positif → alternance correcte
    # de part et d'autre de l'ancre.
    return BIG_WORK if weeks % 2 == 0 else SMALL_WORK


def work_days_for(week_type: str) -> frozenset[str]:
    return _BIG_WORK_DAYS if week_type == BIG_WORK else _SMALL_WORK_DAYS


def is_work_day(d: date) -> bool:
    return DAY_CODES[d.weekday()] in work_days_for(week_type_for(d))


@dataclass(frozen=True)
class DaySchedule:
    date: str
    day_of_week: str
    week_type: str
    is_work_day: bool

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "day_of_week": self.day_of_week,
            "week_type": self.week_type,
            "is_work_day": self.is_work_day,
            # libellé d'entraînement dérivé, pratique pour l'UI
            "training_slot": "service" if self.is_work_day else "off",
        }


def day_schedule(d: date) -> DaySchedule:
    wt = week_type_for(d)
    return DaySchedule(
        date=d.isoformat(),
        day_of_week=DAY_CODES[d.weekday()],
        week_type=wt,
        is_work_day=DAY_CODES[d.weekday()] in work_days_for(wt),
    )


def week_schedule(d: date) -> dict:
    """Vue Lundi→Dimanche de la semaine contenant `d`."""
    monday = _monday_of(d)
    wt = week_type_for(monday)
    days = [day_schedule(monday + timedelta(days=i)).to_dict() for i in range(7)]
    return {
        "monday": monday.isoformat(),
        "week_type": wt,
        "work_days": sorted(work_days_for(wt)),
        "off_days": [c for c in DAY_CODES if c not in work_days_for(wt)],
        "days": days,
    }
