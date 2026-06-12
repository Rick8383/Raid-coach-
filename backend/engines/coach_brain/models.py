from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Discipline(str, Enum):
    RUN = "run"
    CROSSFIT = "crossfit"
    STRENGTH = "strength"
    SWIM = "swim"
    RECOVERY = "recovery"
    REST = "rest"


class WeekType(str, Enum):
    BIG_WORK = "big_work"      # grande semaine police (5 jours travaillés)
    SMALL_WORK = "small_work"  # petite semaine police (2 jours travaillés)


class BudgetStatus(str, Enum):
    UNDER = "under_budget"
    ON_TRACK = "on_track"
    NEAR_LIMIT = "near_limit"
    OVER = "over_budget"


@dataclass(slots=True)
class SessionLoad:
    discipline: Discipline
    duration_min: int
    intensity: float  # 1-10 RPE
    terrain_factor: float = 1.0  # 1.0 flat, up to 1.3 mountain
    load_carried_kg: float = 0.0

    def validate(self) -> None:
        if not 0 < self.duration_min <= 300:
            raise ValueError("duration out of bounds")
        if not 1 <= self.intensity <= 10:
            raise ValueError("intensity out of bounds")
        if not 1.0 <= self.terrain_factor <= 1.5:
            raise ValueError("terrain_factor out of bounds")
        if not 0 <= self.load_carried_kg <= 40:
            raise ValueError("load_carried out of bounds")

    @property
    def stress_units(self) -> float:
        """TSS-like: duration × (RPE/10)² × terrain × load bonus."""
        load_bonus = 1 + max(0.0, self.load_carried_kg - 5) * 0.015
        return round(self.duration_min * (self.intensity / 10) ** 2
                     * self.terrain_factor * load_bonus, 1)


@dataclass(slots=True, frozen=True)
class WeeklyBudget:
    week_type: WeekType
    total_budget_su: float
    per_discipline_cap: dict[str, float]
    hard_sessions_cap: int


@dataclass(slots=True, frozen=True)
class BudgetReport:
    status: BudgetStatus
    consumed_su: float
    budget_su: float
    remaining_su: float
    consumed_pct: float
    per_discipline_su: dict[str, float]
    hard_sessions_done: int
    warnings: list[str]


@dataclass(slots=True)
class TrainingGoal:
    goal_id: str
    name: str
    discipline: Discipline
    target_date_weeks: int  # weeks from now
    priority: int  # 1 = highest (user-defined)

    def validate(self) -> None:
        if self.target_date_weeks < 0:
            raise ValueError("target_date_weeks must be >= 0")
        if not 1 <= self.priority <= 5:
            raise ValueError("priority 1-5")


@dataclass(slots=True, frozen=True)
class ArbitrationResult:
    primary_goal_id: str
    ranked_goal_ids: list[str]
    allocation_pct: dict[str, float]  # goal_id -> share of weekly quality work
    rationale: list[str]


@dataclass(slots=True)
class DailyContext:
    day_of_week: str  # "mon".."sun"
    is_work_day: bool
    week_type: WeekType
    readiness: float  # 0-100
    fatigue: float  # 0-100
    sleep_quality: float  # 0-100
    pain_flag: bool
    sciatic_flare: bool  # L5-S1 specific flag
    budget_consumed_pct: float  # 0-150
    days_since_rest: int
    last_two_disciplines: list[str]
    weeks_to_main_goal: int | None = None

    def validate(self) -> None:
        for v, n in [(self.readiness, "readiness"), (self.fatigue, "fatigue"),
                     (self.sleep_quality, "sleep_quality")]:
            if not 0 <= v <= 100:
                raise ValueError(f"{n} out of bounds")
        if not 0 <= self.budget_consumed_pct <= 200:
            raise ValueError("budget_consumed_pct out of bounds")
        if self.days_since_rest < 0:
            raise ValueError("days_since_rest >= 0")
        if self.day_of_week not in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            raise ValueError("invalid day")


@dataclass(slots=True, frozen=True)
class DailyDecision:
    best_action: Discipline
    secondary_action: Discipline | None
    duration_min: int
    intensity_cap: float  # max RPE allowed
    reason: str
    alternatives: list[str]
    safety_notes: list[str]

    def validate(self) -> None:
        if not 0 <= self.duration_min <= 240:
            raise ValueError("duration out of bounds")
        if not 1 <= self.intensity_cap <= 10:
            raise ValueError("intensity_cap out of bounds")
