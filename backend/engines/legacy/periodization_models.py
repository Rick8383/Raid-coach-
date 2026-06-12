from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class CyclePhase(str, Enum):
    BASE = "base"
    BUILD = "build"
    INTENSIFICATION = "intensification"
    DELOAD = "deload"
    TAPER = "taper"
    PEAK = "peak"

class WeekFocus(str, Enum):
    AEROBIC = "aerobic"
    STRENGTH = "strength"
    MIXED = "mixed"
    SPEED = "speed"
    TECHNICAL = "technical"
    RECOVERY = "recovery"
    TEST = "test"

@dataclass(slots=True, frozen=True)
class PeriodizationContext:
    sport: str
    goal: str
    weeks: int
    sessions_per_week: int
    current_fitness: float
    fatigue: float
    target_event: str | None = None
    priority: str = "balanced"

    def validate(self) -> None:
        if self.weeks < 4:
            raise ValueError("weeks must be >= 4")
        if self.sessions_per_week < 2:
            raise ValueError("sessions_per_week must be >= 2")
        if not 0 <= self.current_fitness <= 100:
            raise ValueError("current_fitness must be between 0 and 100")
        if not 0 <= self.fatigue <= 100:
            raise ValueError("fatigue must be between 0 and 100")

@dataclass(slots=True, frozen=True)
class TrainingWeek:
    week_number: int
    phase: CyclePhase
    focus: WeekFocus
    sessions_planned: int
    volume_factor: float
    intensity_factor: float
    deload: bool = False
    notes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.week_number <= 0:
            raise ValueError("week_number must be positive")
        if self.sessions_planned <= 0:
            raise ValueError("sessions_planned must be positive")
        if self.volume_factor <= 0:
            raise ValueError("volume_factor must be positive")
        if self.intensity_factor <= 0:
            raise ValueError("intensity_factor must be positive")

@dataclass(slots=True, frozen=True)
class PeriodizationPlan:
    plan_id: str
    sport: str
    goal: str
    weeks: list[TrainingWeek]

    def validate(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id is required")
        if not self.weeks:
            raise ValueError("weeks are required")
        for week in self.weeks:
            week.validate()
