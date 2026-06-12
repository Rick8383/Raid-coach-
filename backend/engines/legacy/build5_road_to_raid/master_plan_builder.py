
from __future__ import annotations

from .models import MasterPlan, RaidScoreResult
from .periodization_engine import PeriodizationEngine


class MasterPlanBuilder:
    """Build 5F — Create the high-level Road To RAID master plan."""

    def __init__(self) -> None:
        self.periodization = PeriodizationEngine()

    def build(self, score: RaidScoreResult, duration_weeks: int = 16, goal: str = "mountain_raid") -> MasterPlan:
        phases = self.periodization.build_phases(duration_weeks)
        return MasterPlan(
            duration_weeks=duration_weeks,
            phases=phases,
            goal=goal,
            raid_score=score.score,
        )
