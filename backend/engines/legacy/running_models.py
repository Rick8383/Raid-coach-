from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class RunningFamilyType(str, Enum):
    EASY = "easy"
    ENDURANCE = "endurance"
    TEMPO = "tempo"
    THRESHOLD = "threshold"
    INTERVAL = "interval"
    HILL = "hill"
    TRAIL = "trail"
    RAID = "raid"
    RECOVERY = "recovery"
    LONG_RUN = "long_run"

LEVELS = ["beginner", "intermediate", "advanced", "deload", "race_prep", "elite"]

@dataclass(slots=True, frozen=True)
class RunBlock:
    name: str
    duration_min: int
    intensity: str
    terrain: str
    distance_km: float | None = None
    elevation_m: int | None = None
    reps: int | None = None
    notes: str = ""

@dataclass(slots=True, frozen=True)
class RunningFamily:
    family_id: str
    name: str
    family_type: RunningFamilyType
    base_duration_min: int
    terrain_tags: list[str] = field(default_factory=list)
    pattern_tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class RunningTemplate:
    template_id: str
    family_id: str
    level: str
    duration_min: int
    expected_load: float
    blocks: list[RunBlock]
    tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class GeneratedRunWorkout:
    workout_id: str
    family_id: str
    template_id: str
    duration_min: int
    expected_load: float
    blocks: list[RunBlock]
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
            raise ValueError("at least one run block is required")
