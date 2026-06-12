from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class NutritionPhase(str, Enum):
    RECOMP = "recomp"          # perdre du gras en gagnant du muscle (objectif actuel)
    BUILD = "build"            # léger surplus, prise de muscle
    MAINTAIN = "maintain"
    PEAK = "peak"              # affûtage pré-test
    RACE_WEEK = "race_week"    # semaine de sélection / compétition
    RECOVERY = "recovery"


class DayType(str, Enum):
    HIGH = "high_carb"     # jour double séance / séance dure
    MEDIUM = "medium_carb"  # jour séance unique
    LOW = "low_carb"        # jour repos / récup


class ActivityLevel(str, Enum):
    REST = "rest"
    LIGHT = "light"          # 1 séance facile
    MODERATE = "moderate"    # 1 séance qualité
    HIGH = "high"            # double séance
    EXTREME = "extreme"      # journée type simulation sélection


@dataclass(slots=True)
class NutritionProfile:
    weight_kg: float
    height_cm: float
    age: int
    sex: str  # "m" | "f"
    body_fat_pct: float | None
    target_weight_kg: float
    phase: NutritionPhase

    def validate(self) -> None:
        if not 40 <= self.weight_kg <= 180:
            raise ValueError("weight out of bounds")
        if not 140 <= self.height_cm <= 220:
            raise ValueError("height out of bounds")
        if not 14 <= self.age <= 80:
            raise ValueError("age out of bounds")
        if self.sex not in ("m", "f"):
            raise ValueError("sex must be m/f")
        if self.body_fat_pct is not None and not 3 <= self.body_fat_pct <= 50:
            raise ValueError("body_fat out of bounds")


@dataclass(slots=True, frozen=True)
class MacroTarget:
    day_type: DayType
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    water_l: float
    notes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 1200 <= self.calories <= 6000:
            raise ValueError("calories out of bounds")
        computed = self.protein_g * 4 + self.carbs_g * 4 + self.fat_g * 9
        if abs(computed - self.calories) > self.calories * 0.08:
            raise ValueError(f"macros inconsistent with calories ({computed} vs {self.calories})")


@dataclass(slots=True, frozen=True)
class RaceDayPlan:
    day_minus_1: list[str]
    morning: list[str]
    during: list[str]
    after: list[str]
    hydration: list[str]


@dataclass(slots=True, frozen=True)
class SupplementAdvice:
    name: str
    dose: str
    timing: str
    evidence: str  # "forte" | "modérée"
    rationale: str
