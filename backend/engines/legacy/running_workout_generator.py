from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from running_models import GeneratedRunWorkout
from running_template_factory import build_all_running_templates

@dataclass(slots=True)
class RunningGenerationContext:
    readiness: float = 75
    fatigue: float = 35
    available_time_min: int = 60
    preferred_level: str = "intermediate"
    preferred_terrain: str | None = None

class RunningWorkoutGenerator:
    def __init__(self) -> None:
        self.templates = build_all_running_templates()

    def generate(self, context: RunningGenerationContext) -> GeneratedRunWorkout:
        candidates = [t for t in self.templates if t.duration_min <= context.available_time_min]

        if context.preferred_terrain:
            terrain_matches = [t for t in candidates if context.preferred_terrain in t.tags]
            if terrain_matches:
                candidates = terrain_matches

        if context.fatigue > 70:
            candidates = [t for t in candidates if t.level not in {"race_prep", "elite"} and "interval" not in t.tags]

        if context.readiness < 45:
            candidates = [t for t in candidates if t.level in {"deload", "beginner"} or "recovery" in t.tags]

        preferred = [t for t in candidates if t.level == context.preferred_level]
        if preferred:
            candidates = preferred

        if not candidates:
            raise ValueError("No Running template available for this context")

        template = sorted(candidates, key=lambda t: (t.duration_min, t.expected_load, t.family_id))[0]

        workout = GeneratedRunWorkout(
            workout_id=f"run_{uuid4().hex[:10]}",
            family_id=template.family_id,
            template_id=template.template_id,
            duration_min=template.duration_min,
            expected_load=template.expected_load,
            blocks=template.blocks,
            tags=template.tags,
        )
        workout.validate()
        return workout
