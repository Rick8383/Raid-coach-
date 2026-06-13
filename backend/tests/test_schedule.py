"""Tests du planning police 3/2/2/3 et de son ancrage calendaire.

Ancre verrouillée : la semaine du lundi 15/06/2026 est une GRANDE semaine.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.schedule import (BIG_WORK, SMALL_WORK, day_schedule, is_work_day,
                              week_schedule, week_type_for)


def test_anchor_week_is_big_work():
    assert week_type_for(date(2026, 6, 15)) == BIG_WORK


def test_weeks_alternate_around_anchor():
    assert week_type_for(date(2026, 6, 8)) == SMALL_WORK    # semaine précédente
    assert week_type_for(date(2026, 6, 22)) == SMALL_WORK   # semaine suivante
    assert week_type_for(date(2026, 6, 29)) == BIG_WORK     # +2 semaines


def test_today_13_06_is_small_off():
    # 13/06/2026 = samedi, petite semaine → jour OFF (entraînement)
    d = day_schedule(date(2026, 6, 13))
    assert d.day_of_week == "sat"
    assert d.week_type == SMALL_WORK
    assert d.is_work_day is False


def test_big_week_service_days():
    # Grande semaine : service lun/mar/ven/sam/dim, OFF mer/jeu
    assert is_work_day(date(2026, 6, 15)) is True   # lundi
    assert is_work_day(date(2026, 6, 16)) is True   # mardi
    assert is_work_day(date(2026, 6, 17)) is False  # mercredi OFF
    assert is_work_day(date(2026, 6, 18)) is False  # jeudi OFF
    assert is_work_day(date(2026, 6, 19)) is True   # vendredi
    assert is_work_day(date(2026, 6, 21)) is True   # dimanche


def test_small_week_service_days():
    # Petite semaine (22-28/06) : service mer/jeu uniquement
    assert is_work_day(date(2026, 6, 24)) is True   # mercredi
    assert is_work_day(date(2026, 6, 25)) is True   # jeudi
    assert is_work_day(date(2026, 6, 22)) is False  # lundi OFF
    assert is_work_day(date(2026, 6, 28)) is False  # dimanche OFF


def test_week_schedule_shape():
    w = week_schedule(date(2026, 6, 15))
    assert w["week_type"] == BIG_WORK
    assert w["monday"] == "2026-06-15"
    assert [d["day_of_week"] for d in w["days"]] == \
        ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    assert sum(d["is_work_day"] for d in w["days"]) == 5
