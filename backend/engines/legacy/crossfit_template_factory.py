from __future__ import annotations
from crossfit_family_registry import get_families
from crossfit_models import LEVELS, WorkoutBlock, WorkoutTemplate

LEVEL_MULTIPLIERS = {
    "beginner": 0.70,
    "intermediate": 0.85,
    "advanced": 1.00,
    "deload": 0.75,
    "competition": 1.10,
    "elite": 1.25,
}

class CrossFitTemplateFactory:
    def build_all(self) -> list[WorkoutTemplate]:
        templates = []
        for family in get_families():
            templates.extend(self.build_for_family(family))
        return templates

    def build_for_family(self, family) -> list[WorkoutTemplate]:
        return [self._build_template(family, level) for level in LEVELS]

    def _build_template(self, family, level: str) -> WorkoutTemplate:
        multiplier = LEVEL_MULTIPLIERS[level]
        duration = max(12, int(family.base_duration_min * multiplier))
        block = WorkoutBlock(
            name=f"{family.name} {level}",
            duration_min=duration,
            intensity="low" if level == "deload" else ("high" if level in {"competition", "elite"} else "moderate"),
            movements=family.primary_movements,
            pattern_tags=family.pattern_tags,
        )
        return WorkoutTemplate(
            template_id=f"{family.family_id}_{level}",
            family_id=family.family_id,
            category=family.category,
            level=level,
            duration_min=duration,
            expected_load=round(multiplier, 2),
            blocks=[block],
            tags=[family.category.value, level, *family.pattern_tags],
        )

def build_all_templates() -> list[WorkoutTemplate]:
    return CrossFitTemplateFactory().build_all()
