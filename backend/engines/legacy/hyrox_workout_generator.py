from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from hyrox_models import GeneratedHyroxWorkout
from hyrox_template_factory import build_all_hyrox_templates

@dataclass(slots=True)
class HyroxGenerationContext:
    readiness: float = 75
    fatigue: float = 35
    available_time_min: int = 60
    preferred_level: str = "intermediate"

class HyroxWorkoutGenerator:
    def __init__(self) -> None:
        self.templates = build_all_hyrox_templates()

    def generate(self, context: HyroxGenerationContext) -> GeneratedHyroxWorkout:
        candidates = [t for t in self.templates if t.duration_min <= context.available_time_min]

        if context.fatigue > 70:
            candidates = [t for t in candidates if t.level not in {"competition", "elite"} and "competition" not in t.tags]

        if context.readiness < 45:
            candidates = [t for t in candidates if t.level in {"deload", "beginner"}]

        preferred = [t for t in candidates if t.level == context.preferred_level]
        if preferred:
            candidates = preferred

        if not candidates:
            raise ValueError("No Hyrox template available for this context")

        template = sorted(candidates, key=lambda t: (t.duration_min, t.expected_load, t.family_id))[0]

        workout = GeneratedHyroxWorkout(
            workout_id=f"hyrox_{uuid4().hex[:10]}",
            family_id=template.family_id,
            template_id=template.template_id,
            duration_min=template.duration_min,
            expected_load=template.expected_load,
            blocks=template.blocks,
            tags=template.tags,
        )
        workout.validate()
        return workout
