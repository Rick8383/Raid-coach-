from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class HyroxStation(str, Enum):
    SKIERG = "skierg"
    SLED_PUSH = "sled_push"
    SLED_PULL = "sled_pull"
    BURPEE_BROAD_JUMP = "burpee_broad_jump"
    ROW = "row"
    FARMER_CARRY = "farmer_carry"
    SANDBAG_LUNGE = "sandbag_lunge"
    WALL_BALL = "wall_ball"
    RUN = "run"

LEVELS = ["beginner", "intermediate", "advanced", "deload", "competition", "elite"]

@dataclass(slots=True, frozen=True)
class HyroxBlock:
    station: HyroxStation
    distance_m: int | None = None
    reps: int | None = None
    load_kg: int | None = None
    duration_min: int = 0
    notes: str = ""

@dataclass(slots=True, frozen=True)
class HyroxFamily:
    family_id: str
    name: str
    stations: list[HyroxStation]
    base_duration_min: int
    required_equipment: list[str] = field(default_factory=list)
    pattern_tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class HyroxTemplate:
    template_id: str
    family_id: str
    level: str
    duration_min: int
    expected_load: float
    blocks: list[HyroxBlock]
    tags: list[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class GeneratedHyroxWorkout:
    workout_id: str
    family_id: str
    template_id: str
    duration_min: int
    expected_load: float
    blocks: list[HyroxBlock]
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
