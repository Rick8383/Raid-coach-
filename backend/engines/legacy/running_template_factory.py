from __future__ import annotations
from running_family_registry import get_running_families
from running_models import LEVELS, RunBlock, RunningTemplate

LEVEL_MULTIPLIERS = {
    "beginner": 0.70,
    "intermediate": 0.85,
    "advanced": 1.00,
    "deload": 0.70,
    "race_prep": 1.10,
    "elite": 1.25,
}

class RunningTemplateFactory:
    def build_all(self) -> list[RunningTemplate]:
        templates = []
        for family in get_running_families():
            templates.extend(self.build_for_family(family))
        return templates

    def build_for_family(self, family) -> list[RunningTemplate]:
        return [self._build_template(family, level) for level in LEVELS]

    def _build_template(self, family, level: str) -> RunningTemplate:
        multiplier = LEVEL_MULTIPLIERS[level]
        duration = max(20, int(family.base_duration_min * multiplier))
        terrain = family.terrain_tags[0] if family.terrain_tags else "road"

        block = RunBlock(
            name=f"{family.name} {level}",
            duration_min=duration,
            intensity=self._intensity_for_level(level, family.family_type.value),
            terrain=terrain,
            distance_km=round(duration / 6.0, 1),
            elevation_m=self._elevation_for_terrain(terrain, duration),
            reps=self._reps_for_type(family.family_type.value),
            notes=f"{family.family_type.value} / {level}",
        )

        return RunningTemplate(
            template_id=f"{family.family_id}_{level}",
            family_id=family.family_id,
            level=level,
            duration_min=duration,
            expected_load=round(multiplier, 2),
            blocks=[block],
            tags=["running", level, family.family_type.value, *family.terrain_tags, *family.pattern_tags],
        )

    def _intensity_for_level(self, level: str, family_type: str) -> str:
        if level == "deload" or family_type == "recovery":
            return "low"
        if family_type in {"interval", "threshold", "hill"}:
            return "high" if level in {"advanced", "race_prep", "elite"} else "moderate-high"
        if family_type == "tempo":
            return "moderate-high"
        return "moderate"

    def _elevation_for_terrain(self, terrain: str, duration: int) -> int:
        if terrain in {"hill", "mountain"}:
            return int(duration * 8)
        if terrain in {"trail", "technical", "downhill"}:
            return int(duration * 5)
        if terrain == "mixed":
            return int(duration * 3)
        return int(duration * 1)

    def _reps_for_type(self, family_type: str) -> int | None:
        if family_type in {"interval", "hill", "threshold", "tempo"}:
            return 6
        return None

def build_all_running_templates() -> list[RunningTemplate]:
    return RunningTemplateFactory().build_all()
