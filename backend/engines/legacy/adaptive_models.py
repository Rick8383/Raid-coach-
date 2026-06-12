from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class AdaptationDecision(str, Enum):
    RECOVERY = "recovery"
    DELOAD = "deload"
    MAINTAIN = "maintain"
    PROGRESS = "progress"
    INTENSIFY = "intensify"

@dataclass(slots=True, frozen=True)
class AthleteContext:
    sport: str
    goal: str
    readiness: float
    fatigue: float
    recent_volume: float
    recent_intensity: float
    available_time_min: int
    training_age_months: int
    injury_risk: float = 0
    sleep_hours: float | None = None
    stress_score: float | None = None
    last_sessions: list[str] = field(default_factory=list)

    def validate(self) -> None:
        for field_name in ["readiness", "fatigue", "recent_volume", "recent_intensity", "injury_risk"]:
            value = getattr(self, field_name)
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be between 0 and 100")
        if self.available_time_min <= 0:
            raise ValueError("available_time_min must be positive")
        if self.training_age_months < 0:
            raise ValueError("training_age_months must be positive or zero")

@dataclass(slots=True, frozen=True)
class AdaptationOutput:
    decision: AdaptationDecision
    volume_factor: float
    intensity_factor: float
    duration_cap_min: int
    preferred_level: str
    reason_codes: list[str]
    warnings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.volume_factor <= 0:
            raise ValueError("volume_factor must be positive")
        if self.intensity_factor <= 0:
            raise ValueError("intensity_factor must be positive")
        if self.duration_cap_min <= 0:
            raise ValueError("duration_cap_min must be positive")
        if not self.preferred_level:
            raise ValueError("preferred_level is required")
