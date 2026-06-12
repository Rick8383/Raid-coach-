from .models import PerformanceScore, TrendDirection
from .utils import avg, clamp, slope
class PerformanceScoreEngine:
    def compute(self, performance_scores):
        score=clamp(avg(performance_scores[-6:],50)); s=slope(performance_scores[-6:])
        trend=TrendDirection.IMPROVING if s>0.8 else TrendDirection.DECLINING if s<-0.8 else TrendDirection.STABLE
        return PerformanceScore(score,trend)
