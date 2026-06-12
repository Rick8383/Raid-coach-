from .models import ReadinessScore, TrendDirection
from .utils import avg, clamp, slope
class ReadinessScoreEngine:
    def compute(self, readiness_scores, recovery_scores):
        score=clamp(avg(readiness_scores[-7:],50)*0.6+avg(recovery_scores[-7:],50)*0.4); s=slope(readiness_scores[-7:])
        trend=TrendDirection.IMPROVING if s>1 else TrendDirection.DECLINING if s<-1 else TrendDirection.STABLE
        return ReadinessScore(score,trend)
