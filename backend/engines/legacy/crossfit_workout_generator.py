from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from crossfit_models import GeneratedWorkout, WorkoutTemplate
from crossfit_template_factory import build_all_templates

@dataclass(slots=True)
class WorkoutGenerationContext:
    goal: str = "crossfit"
    readiness: float = 75
    fatigue: float = 35
    available_time_min: int = 60
    preferred_level: str = "intermediate"

class CrossFitWorkoutGenerator:
    def __init__(self) -> None:
        self.templates = build_all_templates()

    def generate(self, context: WorkoutGenerationContext) -> GeneratedWorkout:
        candidates = [t for t in self.templates if t.duration_min <= context.available_time_min]

        if context.fatigue > 70:
            candidates = [t for t in candidates if t.level not in {"competition", "elite"}]

        if context.readiness < 45:
            candidates = [t for t in candidates if t.level in {"deload", "beginner"}]

        preferred = [t for t in candidates if t.level == context.preferred_level]
        if preferred:
            candidates = preferred

        if not candidates:
            raise ValueError("No CrossFit template available for this context")

        template = sorted(candidates, key=lambda t: (t.duration_min, t.expected_load, t.family_id))[0]

        workout = GeneratedWorkout(
            workout_id=f"cf_{uuid4().hex[:10]}",
            category=template.category.value,
            family_id=template.family_id,
            template_id=template.template_id,
            duration_min=template.duration_min,
            expected_load=template.expected_load,
            blocks=template.blocks,
            tags=template.tags,
        )
        workout.validate()
        return workout
