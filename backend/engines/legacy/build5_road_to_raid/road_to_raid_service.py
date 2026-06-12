
from __future__ import annotations

from .daily_generator import DailyGenerator
from .gap_analyzer import GapAnalyzer
from .master_plan_builder import MasterPlanBuilder
from .models import RoadToRaidPlan
from .raid_profiler import RaidProfiler
from .raid_score import RaidScoreEngine
from .weakness_detector import WeaknessDetector
from .week_generator import WeekGenerator


class RoadToRaidService:
    """Build 5 — Full Road To RAID runtime orchestrator."""

    def __init__(self) -> None:
        self.profiler = RaidProfiler()
        self.scorer = RaidScoreEngine()
        self.weakness_detector = WeaknessDetector()
        self.gap_analyzer = GapAnalyzer()
        self.master_plan_builder = MasterPlanBuilder()
        self.week_generator = WeekGenerator()
        self.daily_generator = DailyGenerator()

    def build_plan(
        self,
        duration_weeks: int = 16,
        goal: str = "mountain_raid",
        **profile_inputs: float,
    ) -> RoadToRaidPlan:
        profile = self.profiler.create_profile(**profile_inputs)
        score = self.scorer.compute(profile)
        weaknesses = self.weakness_detector.detect(profile)
        gaps = self.gap_analyzer.analyze(profile, goal)
        master_plan = self.master_plan_builder.build(score, duration_weeks, goal)
        weeks = self.week_generator.generate(master_plan, gaps)
        days = self.daily_generator.generate(weeks)
        return RoadToRaidPlan(
            profile=profile,
            score=score,
            weaknesses=weaknesses,
            gaps=gaps,
            master_plan=master_plan,
            weeks=weeks,
            days=days,
        )
