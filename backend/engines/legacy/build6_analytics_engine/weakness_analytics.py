from .models import WeaknessAnalytics
from .utils import avg, clamp
class WeaknessAnalyticsEngine:
    def analyze(self, weakness_scores):
        if not weakness_scores: return WeaknessAnalytics([],100.0,'none')
        weakest=[d for d,s in sorted(weakness_scores.items(), key=lambda kv:kv[1]) if s<65][:3]; average=clamp(avg(list(weakness_scores.values()),100))
        priority='critical' if any(s<40 for s in weakness_scores.values()) else 'high' if len(weakest)>=2 else 'medium' if weakest else 'low'
        return WeaknessAnalytics(weakest,average,priority)
