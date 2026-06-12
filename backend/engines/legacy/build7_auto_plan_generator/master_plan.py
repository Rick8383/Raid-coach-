
from .models import GoalInput, GapAnalysis, MacroCycle
class MasterPlanEngine:
    def build(self, goal: GoalInput, gaps: GapAnalysis) -> MacroCycle:
        phases=['base','build','specific','taper'] if goal.duration_weeks>8 else ['build','specific','taper']
        obj=f'{goal.goal_type.value}:{goal.target_event}:{goal.target_level}'
        if gaps.primary_gaps: obj+=':gap-focused'
        return MacroCycle(goal.duration_weeks, obj, phases)
