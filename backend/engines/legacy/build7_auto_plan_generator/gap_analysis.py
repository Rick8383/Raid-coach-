
from .models import GapAnalysis, GoalInput
class AutoPlanGapAnalyzer:
    def analyze(self, goal: GoalInput, analytics: dict[str,float]) -> GapAnalysis:
        primary=[]; secondary=[]; risks=[]; constraints=[]
        for key in ['endurance','mountain','portage','speed','technical','recovery']:
            v=analytics.get(key,70)
            if v<55: primary.append(key)
            elif v<70: secondary.append(key)
        if analytics.get('risk',0)>=70: risks.append('high_training_risk')
        if analytics.get('readiness',100)<55: constraints.append('readiness_limited')
        if analytics.get('recovery',100)<55: constraints.append('recovery_limited')
        if not primary and not secondary: secondary.append('race_specificity')
        return GapAnalysis(primary, secondary, constraints, risks)
