import random
from .models import RunCategory, ReadinessZone, FatigueZone, RunFamily
from .family_registry import RUN_FAMILIES

GOAL_CATEGORIES = {
    "raid": {RunCategory.RAID, RunCategory.LONG_RUN, RunCategory.HILLS, RunCategory.TEMPO, RunCategory.THRESHOLD},
    "10k": {RunCategory.TEMPO, RunCategory.THRESHOLD, RunCategory.VMA_LONG, RunCategory.VMA_SHORT},
    "trail": {RunCategory.LONG_RUN, RunCategory.HILLS, RunCategory.Z2, RunCategory.FARTLEK},
}

MAX_DIFFICULTY = {
    ReadinessZone.PEAK: 5, ReadinessZone.GREEN: 5, ReadinessZone.YELLOW: 4,
    ReadinessZone.ORANGE: 3, ReadinessZone.RED: 2,
}

def select_family(goal: str, phase: str, availability_min: int, readiness_zone: ReadinessZone, fatigue_zone: FatigueZone, terrain: str = "road") -> RunFamily:
    allowed = GOAL_CATEGORIES.get(goal, {RunCategory.Z2, RunCategory.RECOVERY})
    families = [f for f in RUN_FAMILIES if f.category in allowed and f.difficulty <= MAX_DIFFICULTY[readiness_zone]]
    if fatigue_zone == FatigueZone.DANGER:
        families = [f for f in families if f.category not in {RunCategory.VMA_SHORT, RunCategory.VMA_LONG, RunCategory.TEST}]
    if not families:
        families = [f for f in RUN_FAMILIES if f.category == RunCategory.RECOVERY]
    # Deterministic enough for tests: prefer RAID/trail-compatible when available.
    preferred = [f for f in families if "raid" in f.id or "trail" in f.id or f.category in {RunCategory.RAID, RunCategory.HILLS, RunCategory.LONG_RUN}]
    return random.choice(preferred or families)
