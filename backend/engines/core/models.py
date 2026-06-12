"""BUILD 1 — Core Domain Model
Source de vérité : Structure_build1.md, Build explication.md, Architecture.rtf
Conformité specs V9/V14 : entités Athlete, Goal, Session, SessionResult,
DailyMetrics, PerformanceSnapshot, RaidProfile, AthleteMemory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4


# ===== ENUMS =====

class GoalType(str, Enum):
    RAID = "raid"
    TRAIL = "trail"
    HYROX = "hyrox"
    CROSSFIT = "crossfit"
    RUN_10K = "run_10k"
    RUN_SEMI = "run_semi"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SessionType(str, Enum):
    RUN = "run"
    CROSSFIT = "crossfit"
    STRENGTH = "strength"
    SWIM = "swim"
    RECOVERY = "recovery"
    HYBRID = "hybrid"


class ReadinessZone(str, Enum):
    PEAK = "peak"         # ≥ 90
    GREEN = "green"       # ≥ 75
    YELLOW = "yellow"     # ≥ 60
    ORANGE = "orange"     # ≥ 40
    RED = "red"           # < 40


class FatigueZone(str, Enum):
    OPTIMAL = "optimal"   # ACWR ≤ 1.2
    WARNING = "warning"   # ACWR ≤ 1.4
    DANGER = "danger"     # ACWR > 1.4


# ===== BUILD 1.1 — ATHLETE =====

@dataclass
class Athlete:
    id: UUID = field(default_factory=uuid4)
    firstname: str = ""
    lastname: str = ""
    birth_date: date | None = None
    weight_kg: float = 75.0
    height_cm: float = 172.0
    resting_hr: int | None = None
    max_hr: int | None = None
    vo2max: float | None = None
    vma: float | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        if not 30 <= self.weight_kg <= 200:
            raise ValueError("weight_kg out of bounds")
        if not 100 <= self.height_cm <= 250:
            raise ValueError("height_cm out of bounds")
        if self.max_hr is not None and not 120 <= self.max_hr <= 230:
            raise ValueError("max_hr out of bounds")
        if self.vma is not None and not 5 <= self.vma <= 30:
            raise ValueError("vma out of bounds")

    @property
    def age(self) -> int | None:
        if self.birth_date is None:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def bmi(self) -> float:
        return round(self.weight_kg / (self.height_cm / 100) ** 2, 1)


# ===== BUILD 1.2 — GOAL =====

@dataclass
class Goal:
    id: UUID = field(default_factory=uuid4)
    athlete_id: UUID = field(default_factory=uuid4)
    goal_type: GoalType = GoalType.RAID
    target_date: date | None = None
    priority: int = 1
    status: GoalStatus = GoalStatus.ACTIVE
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be 1-5")
        if self.target_date is not None and self.target_date < date.today():
            raise ValueError("target_date must be in the future")

    @property
    def weeks_to_target(self) -> int | None:
        if self.target_date is None:
            return None
        delta = (self.target_date - date.today()).days
        return max(0, delta // 7)


# ===== BUILD 1.3 — SESSION =====

@dataclass
class Session:
    id: UUID = field(default_factory=uuid4)
    athlete_id: UUID = field(default_factory=uuid4)
    session_type: SessionType = SessionType.RUN
    family: str = ""
    planned_duration_min: int = 60
    planned_load: float = 0.0
    date: date = field(default_factory=date.today)
    status: str = "planned"  # planned | done | skipped | modified
    detail_json: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not 0 < self.planned_duration_min <= 300:
            raise ValueError("planned_duration_min out of bounds")
        if self.planned_load < 0:
            raise ValueError("planned_load must be >= 0")


# ===== BUILD 1.4 — SESSION RESULT =====

@dataclass
class SessionResult:
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    duration_min: int = 0
    rpe: int = 5
    completed: bool = True
    notes: str = ""
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        if not 1 <= self.rpe <= 10:
            raise ValueError("rpe must be 1-10")
        if not 0 <= self.duration_min <= 480:
            raise ValueError("duration_min out of bounds")


# ===== BUILD 1.5 — DAILY METRICS =====

@dataclass
class DailyMetrics:
    id: UUID = field(default_factory=uuid4)
    athlete_id: UUID = field(default_factory=uuid4)
    date: date = field(default_factory=date.today)
    sleep_hours: float = 7.0
    sleep_quality: float = 70.0   # 0-100
    fatigue: float = 40.0          # 0-100
    stress: float = 40.0           # 0-100
    soreness: float = 30.0         # 0-100
    motivation: float = 70.0       # 0-100
    recovery: float = 70.0         # 0-100
    readiness_score: float = 0.0   # calculé
    pain_flag: bool = False
    sciatic_flare: bool = False
    hrv: float | None = None
    resting_hr: int | None = None
    weight_kg: float | None = None
    notes: str = ""

    def validate(self) -> None:
        for attr in ("sleep_quality", "fatigue", "stress", "soreness",
                     "motivation", "recovery"):
            v = getattr(self, attr)
            if not 0 <= v <= 100:
                raise ValueError(f"{attr} must be 0-100 (got {v})")
        if not 0 <= self.sleep_hours <= 24:
            raise ValueError("sleep_hours out of bounds")


# ===== BUILD 1.6 — PERFORMANCE SNAPSHOT =====

@dataclass
class PerformanceSnapshot:
    id: UUID = field(default_factory=uuid4)
    athlete_id: UUID = field(default_factory=uuid4)
    date: date = field(default_factory=date.today)
    vo2max: float | None = None
    threshold_pace_sec_km: int | None = None  # allure seuil, sec/km
    raid_score: float = 0.0
    fitness_score: float = 0.0
    fatigue_score: float = 0.0
    readiness_score: float = 0.0
    cooper_m: int | None = None
    vma_kmh: float | None = None

    def validate(self) -> None:
        for attr in ("raid_score", "fitness_score", "fatigue_score", "readiness_score"):
            v = getattr(self, attr)
            if not 0 <= v <= 100:
                raise ValueError(f"{attr} must be 0-100")
        if self.vma_kmh is not None and not 5 <= self.vma_kmh <= 30:
            raise ValueError("vma_kmh out of bounds")


# ===== BUILD 1.7 — RAID PROFILE =====

@dataclass
class RaidProfile:
    athlete_id: UUID = field(default_factory=uuid4)
    endurance_score: float = 0.0   # 30% weight
    mountain_score: float = 0.0    # 20% weight
    carry_score: float = 0.0       # 20% weight
    strength_score: float = 0.0    # 15% weight
    resilience_score: float = 0.0  # 15% weight
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        for attr in ("endurance_score", "mountain_score", "carry_score",
                     "strength_score", "resilience_score"):
            v = getattr(self, attr)
            if not 0 <= v <= 100:
                raise ValueError(f"{attr} must be 0-100")

    @property
    def raid_score(self) -> float:
        return round(
            self.endurance_score * 0.30 +
            self.mountain_score  * 0.20 +
            self.carry_score     * 0.20 +
            self.strength_score  * 0.15 +
            self.resilience_score * 0.15, 1)

    @property
    def weakest_axis(self) -> str:
        axes = {
            "endurance": self.endurance_score,
            "mountain": self.mountain_score,
            "carry": self.carry_score,
            "strength": self.strength_score,
            "resilience": self.resilience_score,
        }
        return min(axes, key=axes.get)


# ===== BUILD 1.8 — ATHLETE MEMORY =====

@dataclass
class AthleteMemory:
    athlete_id: UUID = field(default_factory=uuid4)
    preferred_families: list[str] = field(default_factory=list)
    avoided_families: list[str] = field(default_factory=list)
    best_blocks: list[str] = field(default_factory=list)
    worst_blocks: list[str] = field(default_factory=list)
    response_profile: dict = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def record_response(self, family_id: str, rpe_felt: float,
                        rpe_planned: float) -> None:
        """Update response profile after a session."""
        diff = round(rpe_felt - rpe_planned, 1)
        existing = self.response_profile.get(family_id, {"count": 0, "avg_rpe_diff": 0.0})
        n = existing["count"]
        new_avg = (existing["avg_rpe_diff"] * n + diff) / (n + 1)
        self.response_profile[family_id] = {
            "count": n + 1, "avg_rpe_diff": round(new_avg, 2)}
        if diff > 1.5 and family_id not in self.avoided_families:
            self.avoided_families.append(family_id)
        elif diff < -1.5 and family_id not in self.preferred_families:
            self.preferred_families.append(family_id)
        self.last_updated = datetime.utcnow()
