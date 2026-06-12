from dataclasses import dataclass
from enum import Enum
class TrendDirection(str, Enum):
    IMPROVING="improving"; STABLE="stable"; DECLINING="declining"
class RiskLevel(str, Enum):
    LOW="low"; MODERATE="moderate"; HIGH="high"; CRITICAL="critical"
@dataclass(slots=True)
class AnalyticsInput:
    recent_loads:list[float]; chronic_load:float; readiness_scores:list[float]; recovery_scores:list[float]; performance_scores:list[float]; weakness_scores:dict[str,float]
@dataclass(slots=True)
class FitnessScore: score:float; label:str
@dataclass(slots=True)
class FatigueScore: score:float; acute_chronic_ratio:float; risk_level:RiskLevel
@dataclass(slots=True)
class ReadinessScore: score:float; trend:TrendDirection
@dataclass(slots=True)
class RiskScore: score:float; level:RiskLevel; reasons:list[str]
@dataclass(slots=True)
class PerformanceScore: score:float; trend:TrendDirection
@dataclass(slots=True)
class TrendResult: direction:TrendDirection; delta:float; slope:float
@dataclass(slots=True)
class WeaknessAnalytics: weakest_domains:list[str]; average_weakness_score:float; priority:str
@dataclass(slots=True)
class AnalyticsReport:
    fitness:FitnessScore; fatigue:FatigueScore; readiness:ReadinessScore; risk:RiskScore; performance:PerformanceScore; trend:TrendResult; weaknesses:WeaknessAnalytics; global_status:str
