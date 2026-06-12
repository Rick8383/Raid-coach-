from .models import RunCategory, RunFamily, RunTemplate
from .family_registry import RUN_FAMILIES

LEVELS = ("beginner", "intermediate", "advanced", "deload", "peak", "elite")
LEVEL_MULTIPLIERS = {"beginner":0.70,"intermediate":0.85,"advanced":1.00,"deload":0.75,"peak":0.90,"elite":1.20}
BASE_DURATION = {
    RunCategory.RECOVERY:45, RunCategory.Z2:60, RunCategory.FARTLEK:60, RunCategory.TEMPO:70,
    RunCategory.THRESHOLD:75, RunCategory.VMA_SHORT:60, RunCategory.VMA_LONG:70,
    RunCategory.HILLS:75, RunCategory.LONG_RUN:120, RunCategory.RAID:90, RunCategory.TEST:60,
}

def build_template(family: RunFamily, level: str) -> RunTemplate:
    duration = int(BASE_DURATION[family.category] * LEVEL_MULTIPLIERS[level])
    structure = {
        "warmup_min": max(10, int(duration * 0.2)),
        "main": [{"type": family.category.value, "duration_min": max(15, int(duration * 0.6))}],
        "cooldown_min": max(5, int(duration * 0.1)),
    }
    return RunTemplate(
        id=f"{family.id}_{level}",
        family_id=family.id,
        level=level,
        duration_min=duration,
        structure=structure,
        tags=list(family.tags) + [level],
    )

def build_registry(families: list[RunFamily]) -> list[RunTemplate]:
    return [build_template(f, level) for f in families for level in LEVELS]

ALL_TEMPLATES = build_registry(RUN_FAMILIES)
assert len(ALL_TEMPLATES) == 660
