from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TrainingContext:
    goal: str
    phase: str

    readiness: float
    fatigue: float

    available_time_min: int

    equipment: list[str] = field(default_factory=list)
    terrain: str | None = None

    last_sessions: list[str] = field(default_factory=list)

    sleep_hours: float | None = None
    stress_score: float | None = None
    motivation_score: float | None = None

    def validate(self) -> None:
        if not 0 <= self.readiness <= 100:
            raise ValueError("readiness must be between 0 and 100")
        if not 0 <= self.fatigue <= 100:
            raise ValueError("fatigue must be between 0 and 100")
        if self.available_time_min <= 0:
            raise ValueError("available_time_min must be positive")
