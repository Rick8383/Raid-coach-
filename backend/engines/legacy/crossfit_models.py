from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class CrossFitCategory(str, Enum):
    STRENGTH = "strength"
    GYMNASTICS = "gymnastics"
    METCON = "metcon"
    HYROX = "hyrox"
    TACTICAL = "tactical"

LEVELS = ["beginner", "intermediate", "advanced", "deload", "competition", "elite"]

@dataclass(slots=True, frozen=True)
class CrossFitFamily:
    family_id: str
    name: str
    category: CrossFitCategory
    primary_movements: list[str]
    pattern_tags: list[str]
    base_duration_min: int
    required_equipment: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class WorkoutBlock:
    name: str
    duration_min: int
    intensity: str
    movements: list[str] = field(default_factory=list)
    pattern_tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class WorkoutTemplate:
    template_id: str
    family_id: str
    category: CrossFitCategory
    level: str
    duration_min: int
    expected_load: float
    blocks: list[WorkoutBlock]
    tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
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
            raise ValueError("at least one block is required")
