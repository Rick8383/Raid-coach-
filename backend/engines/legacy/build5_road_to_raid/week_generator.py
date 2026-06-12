
from __future__ import annotations

from .models import MasterPlan, TrainingWeek, PlanPhase, Gap


BASE_SESSIONS = {
    PlanPhase.BUILD: ["Z2 trail", "strength endurance", "technical skills", "easy recovery"],
    PlanPhase.PEAK: ["RAID simulation", "vertical tempo", "loaded carry", "recovery"],
    PlanPhase.TAPER: ["short sharp run", "mobility", "easy trail", "rest"],
    PlanPhase.RACE: ["shakeout", "race prep", "race day", "recovery"],
}


class WeekGenerator:
    """Build 5G — Generate weekly blocks from the master plan and gaps."""

    def generate(self, master_plan: MasterPlan, gaps: list[Gap]) -> list[TrainingWeek]:
        weeks: list[TrainingWeek] = []
        week_number = 1
        priority_focus = [g.domain for g in gaps if g.priority in {"critical", "high"}][:2]

        for phase in master_plan.phases:
            for _ in range(phase.weeks):
                focus = list(dict.fromkeys(phase.focus + priority_focus))
                sessions = BASE_SESSIONS[phase.phase].copy()
                target_load = round(100 * phase.volume_factor * phase.intensity_factor, 1)
                weeks.append(
                    TrainingWeek(
                        week_number=week_number,
                        phase=phase.phase,
                        focus=focus,
                        sessions=sessions,
                        target_load=target_load,
                    )
                )
                week_number += 1
        return weeks
