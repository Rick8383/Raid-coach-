
from .models import AutoPlan
class AdaptivePlanningEngine:
    def attach_rules(self, plan: AutoPlan) -> AutoPlan:
        plan.adaptive_rules.extend(['if readiness < 45 then reduce next 3 days','if recovery < 40 then insert recovery day','if risk >= high then block hard sessions','if weakness critical then preserve one focused session weekly'])
        return plan
