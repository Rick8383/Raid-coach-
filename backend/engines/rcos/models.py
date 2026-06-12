from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class MemoryKind(str, Enum):
    SESSION_RESPONSE = "session_response"    # comment l'athlète a répondu à une séance
    FATIGUE_PATTERN = "fatigue_pattern"      # patterns récurrents (jours, contextes)
    PREFERENCE = "preference"                # préférences implicites/explicites
    INJURY_SIGNAL = "injury_signal"          # signaux précurseurs (sciatique...)
    BREAKTHROUGH = "breakthrough"            # PRs, déblocages


class LifeConstraintKind(str, Enum):
    WORK_SHIFT = "work_shift"
    TRAVEL = "travel"
    FAMILY = "family"
    STRESS_PERIOD = "stress_period"
    ILLNESS = "illness"


class SeasonPhase(str, Enum):
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    SELECTION = "selection"
    TRANSITION = "transition"


@dataclass(slots=True)
class MemoryEntry:
    kind: MemoryKind
    date: str
    summary: str
    weight: float = 1.0     # importance 0-3, décroît avec le temps
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0 <= self.weight <= 3:
            raise ValueError("weight out of bounds")
        if not self.summary:
            raise ValueError("summary required")


@dataclass(slots=True, frozen=True)
class MemoryDigest:
    """Ce que le coach 'sait' de l'athlète, condensé pour la décision."""
    works_well: list[str]
    works_poorly: list[str]
    risk_signals: list[str]
    preferences: list[str]
    recent_breakthroughs: list[str]


@dataclass(slots=True)
class TwinState:
    """Modèle de Banister simplifié : fitness (CTL) / fatigue (ATL) / forme (TSB)."""
    fitness: float = 0.0     # charge chronique (42 j)
    fatigue: float = 0.0     # charge aiguë (7 j)

    @property
    def form(self) -> float:
        return round(self.fitness - self.fatigue, 1)

    def update(self, daily_load_su: float) -> "TwinState":
        if daily_load_su < 0 or daily_load_su > 500:
            raise ValueError("daily_load out of bounds")
        # exponentially weighted moving averages
        self.fitness += (daily_load_su - self.fitness) / 42
        self.fatigue += (daily_load_su - self.fatigue) / 7
        self.fitness = round(self.fitness, 2)
        self.fatigue = round(self.fatigue, 2)
        return self


@dataclass(slots=True)
class LifeConstraint:
    kind: LifeConstraintKind
    date_from: str
    date_to: str
    impact: float  # 0-1, réduction de capacité d'entraînement
    note: str = ""

    def validate(self) -> None:
        if not 0 <= self.impact <= 1:
            raise ValueError("impact 0-1")
        if self.date_from > self.date_to:
            raise ValueError("invalid date range")


@dataclass(slots=True, frozen=True)
class SeasonBlock:
    phase: SeasonPhase
    week_start: int   # semaine relative depuis aujourd'hui
    week_end: int
    focus: str
    target_weekly_su: tuple[float, float]  # (grande semaine, petite semaine)


@dataclass(slots=True, frozen=True)
class AnnualPlan:
    weeks_total: int
    selection_week: int
    blocks: list[SeasonBlock]
    key_milestones: list[str]

    def validate(self) -> None:
        if not self.blocks:
            raise ValueError("empty plan")
        if self.blocks[0].week_start != 0:
            raise ValueError("plan must start at week 0")
        for a, b in zip(self.blocks, self.blocks[1:]):
            if b.week_start != a.week_end + 1:
                raise ValueError("non-contiguous blocks")


@dataclass(slots=True, frozen=True)
class BestActionToday:
    action: str
    why: str
    if_only_one_thing: str
    week_context: str
    season_context: str
    memory_notes: list[str]
    form_state: str  # "fresh" | "neutral" | "fatigued" | "overreached"
