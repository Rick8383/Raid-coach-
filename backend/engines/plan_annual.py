"""Plan annuel — macro-périodisation jusqu'à la sélection RAID 2029.

Réutilise le planificateur RCOS (B14) : cycles BASE(6)→BUILD(5)→PEAK(2)→
TRANSITION(1), TAPER + SELECTION en fin. Enrichit chaque bloc (dates réelles,
volumes SU grande/petite semaine, dominante) et structure les jalons benchmarks.

Ancre calendaire : semaine du lundi 15/06/2026 (grande semaine 3/2/2/3).
Objectif : sélection ~mars 2029.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from engines.rcos import AnnualPlanner

START_ISO = "2026-06-15"   # lundi, ancre 3/2/2/3
GOAL_ISO = "2029-03-01"    # cible sélection

_DOMINANTE = {
    "base": "cardio",            # volume aérobie + gym skills
    "build": "mixte",            # intensité + WODs + force spécifique
    "peak": "specifique_raid",   # benchmarks officiels + simulation
    "transition": "recup",       # décharge / deload de fin de cycle
    "taper": "affutage",
    "selection": "test",
}


def _weeks_between(start: date, goal: date) -> int:
    return max(8, min((goal - start).days // 7, 220))


def build_annual_plan(start_iso: str = START_ISO, goal_iso: str = GOAL_ISO) -> dict:
    start = date.fromisoformat(start_iso)
    goal = date.fromisoformat(goal_iso)
    weeks = _weeks_between(start, goal)
    plan = AnnualPlanner().build(weeks)

    blocks = []
    for i, b in enumerate(plan.blocks, 1):
        grande_su, petite_su = b.target_weekly_su
        phase = b.phase.value
        blocks.append({
            "index": i,
            "phase": phase.upper(),
            "week_start": b.week_start,
            "week_end": b.week_end,
            "start_date": (start + timedelta(weeks=b.week_start)).isoformat(),
            "end_date": (start + timedelta(weeks=b.week_end, days=6)).isoformat(),
            "focus_principal": b.focus,
            "volume_su_grande_semaine": grande_su,
            "volume_su_petite_semaine": petite_su,
            "dominante": _DOMINANTE.get(phase, "mixte"),
            "is_deload": phase in ("transition", "taper"),
        })

    milestones = []
    for m in plan.key_milestones:
        mm = re.match(r"S(\d+):\s*(.*)", m)
        if mm:
            wk = int(mm.group(1))
            milestones.append({
                "week": wk,
                "date": (start + timedelta(weeks=wk)).isoformat(),
                "label": mm.group(2),
            })

    return {
        "goal": "Sélection RAID 2029",
        "goal_date": goal_iso,
        "start_date": start_iso,
        "weeks_total": plan.weeks_total,
        "selection_week": plan.selection_week,
        "phase_cycle": ["BASE(6)", "BUILD(5)", "PEAK(2)", "TRANSITION(1 deload)"],
        "blocks": blocks,
        "milestones": milestones,
    }
