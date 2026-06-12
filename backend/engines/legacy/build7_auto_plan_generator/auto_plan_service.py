
from .adaptive_planning import AdaptivePlanningEngine
from .daily_generator import AutoDailyGenerator
from .gap_analysis import AutoPlanGapAnalyzer
from .goal_ingestion import GoalIngestionEngine
from .macro_cycles import MacroCycleBuilder
from .master_plan import MasterPlanEngine
from .meso_cycles import MesoCycleBuilder
from .models import AutoPlan
from .week_generator import AutoWeekGenerator
class AutoPlanGeneratorService:
    def __init__(self):
        self.goal_ingestion=GoalIngestionEngine(); self.gap_analyzer=AutoPlanGapAnalyzer(); self.master_plan=MasterPlanEngine(); self.macro_builder=MacroCycleBuilder(); self.meso_builder=MesoCycleBuilder(); self.week_generator=AutoWeekGenerator(); self.daily_generator=AutoDailyGenerator(); self.adaptive=AdaptivePlanningEngine()
    def generate_plan(self, goal_type='raid', target_event='A-race', duration_weeks=16, analytics=None) -> AutoPlan:
        analytics=analytics or {}; goal=self.goal_ingestion.ingest(goal_type,target_event,duration_weeks); gaps=self.gap_analyzer.analyze(goal,analytics); macro=self.master_plan.build(goal,gaps)
        if not self.macro_builder.validate(macro): raise ValueError('Invalid macro cycle')
        meso=self.meso_builder.build(macro,gaps); weeks=self.week_generator.generate(meso); days=self.daily_generator.generate(weeks)
        return self.adaptive.attach_rules(AutoPlan(goal,gaps,macro,meso,weeks,days))
