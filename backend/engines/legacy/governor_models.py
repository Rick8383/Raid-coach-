from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class GovernorDecision(str, Enum):
    ALLOW = "ALLOW"
    REDUCE = "REDUCE"
    MODIFY = "MODIFY"
    BLOCK = "BLOCK"

@dataclass(slots=True, frozen=True)
class GovernorInput:
    readiness_score: int
    recovery_score: int
    volume_factor: float = 1.0
    intensity_factor: float = 1.0
    pain_flag: bool = False
    high_risk_movement: bool = False
    recent_load: float = 50

    def validate(self) -> None:
        if not 0 <= self.readiness_score <= 100:
            raise ValueError("readiness_score must be between 0 and 100")
        if not 0 <= self.recovery_score <= 100:
            raise ValueError("recovery_score must be between 0 and 100")
        if self.volume_factor <= 0:
            raise ValueError("volume_factor must be positive")
        if self.intensity_factor <= 0:
            raise ValueError("intensity_factor must be positive")
        if not 0 <= self.recent_load <= 100:
            raise ValueError("recent_load must be between 0 and 100")

@dataclass(slots=True, frozen=True)
class GovernorOutput:
    decision: GovernorDecision
    volume_modifier: float
    intensity_modifier: float
    reason_codes: list[str]
    warnings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.volume_modifier <= 0:
            raise ValueError("volume_modifier must be positive")
        if self.intensity_modifier <= 0:
            raise ValueError("intensity_modifier must be positive")
        if not self.reason_codes:
            raise ValueError("reason_codes are required")
