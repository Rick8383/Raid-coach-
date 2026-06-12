from __future__ import annotations
from periodization_engine import PeriodizationEngine
from periodization_models import PeriodizationContext

class PeriodizationRouter:
    def __init__(self) -> None:
        self.engine = PeriodizationEngine()

    def route(self, context: PeriodizationContext) -> dict:
        plan = self.engine.generate_plan(context)
        return {
            "plan_id": plan.plan_id,
            "sport": plan.sport,
            "goal": plan.goal,
            "weeks": len(plan.weeks),
            "deload_weeks": [w.week_number for w in plan.weeks if w.deload],
            "peak_week": plan.weeks[-1].week_number,
            "phases": [w.phase.value for w in plan.weeks],
        }
