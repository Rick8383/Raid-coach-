
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RaidLevel(str, Enum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETITIVE = "competitive"
    ADVANCED = "advanced"
    ELITE = "elite"


class PlanPhase(str, Enum):
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    RACE = "race"


@dataclass(slots=True)
class RaidProfile:
    endurance: float
    mountain: float
    portage: float
    speed: float
    technical: float
    navigation: float = 50.0
    recovery: float = 70.0

    def values(self) -> dict[str, float]:
        return {
            "endurance": self.endurance,
            "mountain": self.mountain,
            "portage": self.portage,
            "speed": self.speed,
            "technical": self.technical,
            "navigation": self.navigation,
            "recovery": self.recovery,
        }


@dataclass(slots=True)
class RaidScoreResult:
    score: float
    level: RaidLevel
    classification: str
    components: dict[str, float]


@dataclass(slots=True)
class Weakness:
    domain: str
    score: float
    severity: str
    recommendation: str


@dataclass(slots=True)
class Gap:
    domain: str
    current: float
    target: float
    gap: float
    priority: str


@dataclass(slots=True)
class PeriodizationPhase:
    phase: PlanPhase
    weeks: int
    focus: list[str]
    intensity_factor: float
    volume_factor: float


@dataclass(slots=True)
class MasterPlan:
    duration_weeks: int
    phases: list[PeriodizationPhase]
    goal: str
    raid_score: float


@dataclass(slots=True)
class TrainingWeek:
    week_number: int
    phase: PlanPhase
    focus: list[str]
    sessions: list[str]
    target_load: float


@dataclass(slots=True)
class TrainingDay:
    day: int
    week_number: int
    session_type: str
    objective: str
    load: float
    notes: str = ""


@dataclass(slots=True)
class RoadToRaidPlan:
    profile: RaidProfile
    score: RaidScoreResult
    weaknesses: list[Weakness]
    gaps: list[Gap]
    master_plan: MasterPlan
    weeks: list[TrainingWeek]
    days: list[TrainingDay]
