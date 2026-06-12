from .models import RunCategory, ReadinessZone, FatigueZone

VMA = {RunCategory.VMA_SHORT, RunCategory.VMA_LONG}
HARD = {RunCategory.TEMPO, RunCategory.THRESHOLD, RunCategory.HILLS, RunCategory.VMA_SHORT, RunCategory.VMA_LONG, RunCategory.RAID, RunCategory.TEST}

def governor_accept(category: RunCategory, history: list[dict], readiness_zone: ReadinessZone, fatigue_zone: FatigueZone) -> tuple[bool, float, str | None]:
    if readiness_zone == ReadinessZone.RED and category != RunCategory.RECOVERY:
        return False, 0.5, "readiness_red"
    if fatigue_zone == FatigueZone.DANGER and category in HARD:
        return False, 0.7, "fatigue_danger"
    if history:
        last_cat = history[-1].get("category")
        if isinstance(last_cat, str):
            try: last_cat = RunCategory(last_cat)
            except Exception: last_cat = None
        if last_cat in VMA and category in VMA:
            return False, 1.0, "consecutive_vma"
    return True, 1.0, None
