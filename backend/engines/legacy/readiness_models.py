from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class ReadinessDecision(str, Enum):
    GREEN = "green"
    MAINTAIN = "maintain"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"

@dataclass(slots=True, frozen=True)
class DailyReadinessInput:
    sleep_hours: float
    sleep_quality: float
    fatigue: float
    soreness: float
    stress: float
    motivation: float
    recent_rpe: float
    recent_load: float
    hrv_status: str = "unknown"
    resting_hr_delta: float = 0
    pain_flags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0 <= self.sleep_hours <= 14:
            raise ValueError("sleep_hours must be between 0 and 14")
        for name in ["sleep_quality", "fatigue", "soreness", "stress", "motivation", "recent_load"]:
            value = getattr(self, name)
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        if not 0 <= self.recent_rpe <= 10:
            raise ValueError("recent_rpe must be between 0 and 10")

@dataclass(slots=True, frozen=True)
class ReadinessOutput:
    score: int
    decision: ReadinessDecision
    volume_factor: float
    intensity_factor: float
    duration_cap_factor: float
    reason_codes: list[str]
    warnings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100")
        if self.volume_factor <= 0:
            raise ValueError("volume_factor must be positive")
        if self.intensity_factor <= 0:
            raise ValueError("intensity_factor must be positive")
        if self.duration_cap_factor <= 0:
            raise ValueError("duration_cap_factor must be positive")
