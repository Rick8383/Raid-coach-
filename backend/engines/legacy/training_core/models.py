from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WorkoutBlock:
    name: str
    duration_min: int
    intensity: str
    movements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GeneratedWorkout:
    workout_id: str
    category: str
    family_id: str
    template_id: str
    duration_min: int
    expected_load: float
    blocks: list[WorkoutBlock]
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.workout_id:
            raise ValueError("workout_id is required")
        if not self.family_id:
            raise ValueError("family_id is required")
        if not self.template_id:
            raise ValueError("template_id is required")
        if self.duration_min <= 0:
            raise ValueError("duration_min must be positive")
        if self.expected_load <= 0:
            raise ValueError("expected_load must be positive")
        if not self.blocks:
            raise ValueError("at least one workout block is required")
