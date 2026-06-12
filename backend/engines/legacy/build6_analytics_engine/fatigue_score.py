from .models import FatigueScore, RiskLevel
from .utils import avg, clamp
class FatigueScoreEngine:
    def compute(self, recent_loads, chronic_load):
        acute=avg(recent_loads[-7:]); ratio=round(acute/chronic_load,2) if chronic_load>0 else 1.0; score=clamp(ratio*55)
        level=RiskLevel.CRITICAL if ratio>=1.65 else RiskLevel.HIGH if ratio>=1.4 else RiskLevel.MODERATE if ratio>=1.2 else RiskLevel.LOW
        return FatigueScore(score,ratio,level)
