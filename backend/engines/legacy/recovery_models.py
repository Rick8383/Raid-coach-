from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class RecoveryState(str, Enum):
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    CRITICAL = "critical"

class RecoveryRecommendation(str, Enum):
    HIGH_INTENSITY_ALLOWED = "high_intensity_allowed"
    NORMAL_TRAINING = "normal_training"
    REDUCE_VOLUME = "reduce_volume"
    ACTIVE_RECOVERY = "active_recovery"
    REST_DAY = "rest_day"

@dataclass(slots=True, frozen=True)
class RecoveryInput:
    sleep_hours: float
    sleep_quality: float
    fatigue_score: float
    soreness_score: float
    stress_score: float
    last_training_load: float
    days_since_rest: int
    hydration_score: float = 75
    nutrition_score: float = 75
    pain_flags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0 <= self.sleep_hours <= 14:
            raise ValueError("sleep_hours must be between 0 and 14")
        for name in [
            "sleep_quality",
            "fatigue_score",
            "soreness_score",
            "stress_score",
            "last_training_load",
            "hydration_score",
            "nutrition_score",
        ]:
            value = getattr(self, name)
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        if self.days_since_rest < 0:
            raise ValueError("days_since_rest must be positive or zero")

@dataclass(slots=True, frozen=True)
class RecoveryOutput:
    recovery_score: int
    state: RecoveryState
    recommendation: RecoveryRecommendation
    volume_factor: float
    intensity_factor: float
    reason_codes: list[str]
    warnings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0 <= self.recovery_score <= 100:
            raise ValueError("recovery_score must be between 0 and 100")
        if self.volume_factor <= 0:
            raise ValueError("volume_factor must be positive")
        if self.intensity_factor <= 0:
            raise ValueError("intensity_factor must be positive")
