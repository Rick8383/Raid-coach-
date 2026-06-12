from .models import RiskScore, RiskLevel
from .utils import clamp
class RiskScoreEngine:
    def compute(self, fatigue, readiness, recovery_scores):
        reasons=[]; risk=0; rec=recovery_scores[-1] if recovery_scores else readiness.score
        if fatigue.risk_level==RiskLevel.CRITICAL: risk+=45; reasons.append('critical acute/chronic load')
        elif fatigue.risk_level==RiskLevel.HIGH: risk+=35; reasons.append('high acute/chronic load')
        elif fatigue.risk_level==RiskLevel.MODERATE: risk+=18; reasons.append('moderate load warning')
        if readiness.score<45: risk+=35; reasons.append('low readiness')
        elif readiness.score<60: risk+=20; reasons.append('moderate readiness')
        if rec<40: risk+=25; reasons.append('poor recovery')
        score=clamp(risk); level=RiskLevel.CRITICAL if score>=80 else RiskLevel.HIGH if score>=55 else RiskLevel.MODERATE if score>=30 else RiskLevel.LOW
        return RiskScore(score,level,reasons)
