from __future__ import annotations
from uuid import uuid4
from periodization_models import CyclePhase, PeriodizationContext, PeriodizationPlan, TrainingWeek, WeekFocus

class PeriodizationEngine:
    def generate_plan(self, context: PeriodizationContext) -> PeriodizationPlan:
        context.validate()

        weeks = []
        for week_number in range(1, context.weeks + 1):
            phase = self._phase_for_week(week_number, context.weeks)
            deload = self._is_deload_week(week_number, context.weeks, phase)
            focus = self._focus_for_week(context.sport, context.priority, phase, deload)

            volume_factor = self._volume_factor(week_number, context.weeks, phase, deload, context.fatigue)
            intensity_factor = self._intensity_factor(week_number, context.weeks, phase, deload, context.current_fitness)

            sessions = context.sessions_per_week
            if deload:
                sessions = max(2, sessions - 1)
            if phase == CyclePhase.PEAK:
                sessions = max(2, sessions - 1)

            notes = [phase.value, focus.value]
            if deload:
                notes.append("planned_deload")
            if context.fatigue >= 75:
                notes.append("fatigue_guardrail")
            if context.target_event and phase in {CyclePhase.TAPER, CyclePhase.PEAK}:
                notes.append(f"target_event:{context.target_event}")

            weeks.append(TrainingWeek(
                week_number=week_number,
                phase=phase,
                focus=focus,
                sessions_planned=sessions,
                volume_factor=volume_factor,
                intensity_factor=intensity_factor,
                deload=deload,
                notes=notes,
            ))

        plan = PeriodizationPlan(
            plan_id=f"periodization_{uuid4().hex[:10]}",
            sport=context.sport,
            goal=context.goal,
            weeks=weeks,
        )
        plan.validate()
        return plan

    def _phase_for_week(self, week: int, total_weeks: int) -> CyclePhase:
        if week == total_weeks:
            return CyclePhase.PEAK
        if week >= total_weeks - 1:
            return CyclePhase.TAPER
        ratio = week / total_weeks
        if ratio <= 0.35:
            return CyclePhase.BASE
        if ratio <= 0.70:
            return CyclePhase.BUILD
        return CyclePhase.INTENSIFICATION

    def _is_deload_week(self, week: int, total_weeks: int, phase: CyclePhase) -> bool:
        if phase in {CyclePhase.TAPER, CyclePhase.PEAK}:
            return False
        return week % 4 == 0

    def _focus_for_week(self, sport: str, priority: str, phase: CyclePhase, deload: bool) -> WeekFocus:
        if deload:
            return WeekFocus.RECOVERY
        if phase == CyclePhase.BASE:
            return WeekFocus.AEROBIC if sport in {"running", "hyrox"} else WeekFocus.STRENGTH
        if phase == CyclePhase.BUILD:
            return WeekFocus.MIXED
        if phase == CyclePhase.INTENSIFICATION:
            return WeekFocus.SPEED if priority in {"performance", "race"} else WeekFocus.MIXED
        if phase == CyclePhase.TAPER:
            return WeekFocus.TECHNICAL
        return WeekFocus.TEST

    def _volume_factor(self, week: int, total_weeks: int, phase: CyclePhase, deload: bool, fatigue: float) -> float:
        if deload:
            return 0.65
        if phase == CyclePhase.TAPER:
            return 0.55
        if phase == CyclePhase.PEAK:
            return 0.35

        base = 0.85 + (week / total_weeks) * 0.35
        if fatigue >= 75:
            base *= 0.85
        return round(min(base, 1.25), 2)

    def _intensity_factor(self, week: int, total_weeks: int, phase: CyclePhase, deload: bool, fitness: float) -> float:
        if deload:
            return 0.75
        if phase == CyclePhase.TAPER:
            return 0.85
        if phase == CyclePhase.PEAK:
            return 0.95

        base = 0.80 + (week / total_weeks) * 0.30
        if fitness >= 75:
            base += 0.05
        if fitness < 40:
            base -= 0.10
        return round(max(0.65, min(base, 1.20)), 2)
