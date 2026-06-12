from .models import AnalyticsInput, AnalyticsReport, RiskLevel
from .fitness_score import FitnessScoreEngine
from .fatigue_score import FatigueScoreEngine
from .readiness_score import ReadinessScoreEngine
from .risk_score import RiskScoreEngine
from .performance_score import PerformanceScoreEngine
from .trend_analyzer import TrendAnalyzer
from .weakness_analytics import WeaknessAnalyticsEngine
class AnalyticsService:
    def __init__(self):
        self.fitness=FitnessScoreEngine(); self.fatigue=FatigueScoreEngine(); self.readiness=ReadinessScoreEngine(); self.risk=RiskScoreEngine(); self.performance=PerformanceScoreEngine(); self.trend=TrendAnalyzer(); self.weaknesses=WeaknessAnalyticsEngine()
    def analyze(self, data:AnalyticsInput):
        fit=self.fitness.compute(data.recent_loads,data.performance_scores); fat=self.fatigue.compute(data.recent_loads,data.chronic_load); rea=self.readiness.compute(data.readiness_scores,data.recovery_scores); risk=self.risk.compute(fat,rea,data.recovery_scores); perf=self.performance.compute(data.performance_scores); trend=self.trend.analyze(data.performance_scores); weak=self.weaknesses.analyze(data.weakness_scores)
        status='RISK_CONTROL' if risk.level in {RiskLevel.HIGH,RiskLevel.CRITICAL} else 'WEAKNESS_FOCUS' if weak.priority in {'critical','high'} else 'PROGRESSING' if perf.trend.value=='improving' else 'CLEAR'
        return AnalyticsReport(fit,fat,rea,risk,perf,trend,weak,status)
