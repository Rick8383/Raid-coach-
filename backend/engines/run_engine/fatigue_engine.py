from .models import FatigueZone

def fatigue_ratio(acute_load: float, chronic_load: float) -> float:
    if chronic_load <= 0:
        return 1.0
    return round(acute_load / chronic_load, 2)

def fatigue_zone(ratio: float) -> FatigueZone:
    if ratio <= 1.2: return FatigueZone.OPTIMAL
    if ratio <= 1.4: return FatigueZone.WARNING
    return FatigueZone.DANGER
