from .models import ReadinessZone

def readiness_score(sleep: float, fatigue: float, stress: float, motivation: float, recovery: float) -> float:
    # fatigue/stress : scores inversés (100 - x = meilleur si x bas), même
    # sémantique que engines.core.services.ReadinessEngine
    return round(sleep*0.20 + (100 - fatigue)*0.25 + (100 - stress)*0.15
                 + motivation*0.15 + recovery*0.25, 1)

def readiness_zone(score: float) -> ReadinessZone:
    if score >= 90: return ReadinessZone.PEAK
    if score >= 75: return ReadinessZone.GREEN
    if score >= 60: return ReadinessZone.YELLOW
    if score >= 40: return ReadinessZone.ORANGE
    return ReadinessZone.RED
