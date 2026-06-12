from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class StrengthCategory(str, Enum):
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    ASSISTANCE = "assistance"
    OLYMPIC = "olympic"
    RAID_SPECIFIC = "raid_specific"


class ProgressionPhase(str, Enum):
    ACCUMULATION = "accumulation"
    INTENSIFICATION = "intensification"
    PEAKING = "peaking"
    TEST = "test"
    DELOAD = "deload"


class MethodType(str, Enum):
    STANDARD = "standard"
    CLUSTER = "cluster"
    REST_PAUSE = "rest_pause"
    MYO_REPS = "myo_reps"
    DROP_SET = "drop_set"
    CONTRAST = "contrast"
    DYNAMIC_EFFORT = "dynamic_effort"
    EMOM = "emom"
    DENSITY = "density"


class LoadDecision(str, Enum):
    INCREASE = "increase"
    MAINTAIN = "maintain"
    REDUCE = "reduce"
    TECHNIQUE = "technique"
    DELOAD = "deload"


LEVELS = ["beginner", "intermediate", "advanced", "deload", "peaking", "elite"]


@dataclass(slots=True, frozen=True)
class StrengthMovement:
    movement_id: str
    name: str
    category: StrengthCategory
    primary_muscles: list[str]
    equipment: list[str]
    is_bodyweight: bool = False
    raid_relevance: int = 1  # 1-5, 5 = direct RAID test movement


@dataclass(slots=True, frozen=True)
class StrengthBlock:
    movement_id: str
    sets: int
    reps: str  # "5", "8-12", "AMRAP", "max"
    intensity_pct: float | None = None  # % e1RM
    rest_sec: int = 120
    method: MethodType = MethodType.STANDARD
    notes: str = ""


@dataclass(slots=True, frozen=True)
class StrengthFamily:
    family_id: str
    name: str
    category: StrengthCategory
    base_duration_min: int
    pattern_tags: list[str] = field(default_factory=list)
    raid_relevance: int = 1


@dataclass(slots=True, frozen=True)
class StrengthTemplate:
    template_id: str
    family_id: str
    level: str
    duration_min: int
    expected_load: float
    blocks: list[StrengthBlock]
    phase_affinity: list[ProgressionPhase] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class GeneratedStrengthSession:
    session_id: str
    family_id: str
    template_id: str
    level: str
    phase: ProgressionPhase
    duration_min: int
    expected_load: float
    blocks: list[StrengthBlock]
    load_decision: LoadDecision
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.session_id:
            raise ValueError("session_id required")
        if not self.blocks:
            raise ValueError("session must contain blocks")
        if self.duration_min <= 0 or self.duration_min > 180:
            raise ValueError("duration out of bounds")
        if self.expected_load < 0:
            raise ValueError("expected_load must be >= 0")


@dataclass(slots=True)
class PRRecord:
    movement_id: str
    weight_kg: float
    reps: int
    date: str  # ISO
    bodyweight_kg: float | None = None

    def validate(self) -> None:
        if self.weight_kg < 0:
            raise ValueError("weight must be >= 0")
        if self.reps <= 0 or self.reps > 50:
            raise ValueError("reps out of bounds")


@dataclass(slots=True, frozen=True)
class PREstimate:
    movement_id: str
    e1rm: float
    rm3: float
    rm5: float
    rm8: float
    source_weight: float
    source_reps: int


@dataclass(slots=True)
class AdaptiveLoadInput:
    recovery_score: float  # 0-100
    sleep_quality: float  # 0-100
    pain_flag: bool
    hrv_trend: str  # "up" | "stable" | "down"
    run_load_7d: float  # 0-100 normalized
    crossfit_load_7d: float  # 0-100
    strength_load_7d: float  # 0-100
    sessions_since_deload: int

    def validate(self) -> None:
        for v, name in [
            (self.recovery_score, "recovery_score"),
            (self.sleep_quality, "sleep_quality"),
            (self.run_load_7d, "run_load_7d"),
            (self.crossfit_load_7d, "crossfit_load_7d"),
            (self.strength_load_7d, "strength_load_7d"),
        ]:
            if not 0 <= v <= 100:
                raise ValueError(f"{name} out of bounds [0,100]")
        if self.hrv_trend not in ("up", "stable", "down"):
            raise ValueError("invalid hrv_trend")
        if self.sessions_since_deload < 0:
            raise ValueError("sessions_since_deload must be >= 0")


@dataclass(slots=True, frozen=True)
class AdaptiveLoadOutput:
    decision: LoadDecision
    load_modifier: float
    intensity_modifier: float
    reason_codes: list[str]
    warnings: list[str]

    def validate(self) -> None:
        if not 0.2 <= self.load_modifier <= 1.3:
            raise ValueError("load_modifier out of bounds")
        if not 0.2 <= self.intensity_modifier <= 1.3:
            raise ValueError("intensity_modifier out of bounds")


@dataclass(slots=True, frozen=True)
class RaidStrengthTarget:
    movement_id: str
    name: str
    target_value: float
    unit: str  # "reps" | "ratio_bw" | "meters" | "seconds"
    current_value: float
    gap_pct: float
    priority: int  # 1 = highest


@dataclass(slots=True, frozen=True)
class RaidStrengthReport:
    targets: list[RaidStrengthTarget]
    global_readiness_pct: float
    primary_focus: str
    estimated_weeks_to_ready: int
    recommendation: str
