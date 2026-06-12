from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List


class RaidPlanLength(str, Enum):
    WEEKS_8 = "8w"
    WEEKS_12 = "12w"
    WEEKS_16 = "16w"
    WEEKS_24 = "24w"


@dataclass(slots=True)
class RaidProfile:
    endurance: int
    mountain: int
    carry: int
    speed: int
    technical: int


@dataclass(slots=True)
class RaidScore:
    global_score: int
    weakness: str
    readiness_band: str


@dataclass(slots=True)
class RaidWeek:
    week: int
    focus: str
    run_sessions: int
    strength_sessions: int
    long_session_min: int
    carry_work: bool
    elevation_focus: bool


@dataclass(slots=True)
class RoadToRaidPlan:
    plan_length: str
    score: RaidScore
    weeks: List[RaidWeek]
    recommendation: str


def clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def compute_raid_score(profile: RaidProfile) -> RaidScore:
    values: Dict[str, int] = {
        "endurance": clamp(profile.endurance),
        "mountain": clamp(profile.mountain),
        "carry": clamp(profile.carry),
        "speed": clamp(profile.speed),
        "technical": clamp(profile.technical),
    }
    weights = {
        "endurance": 0.30,
        "mountain": 0.25,
        "carry": 0.20,
        "speed": 0.15,
        "technical": 0.10,
    }
    score = round(sum(values[k] * weights[k] for k in values))
    weakness = min(values, key=values.get)
    if score >= 80:
        band = "ready"
    elif score >= 65:
        band = "build"
    elif score >= 45:
        band = "base"
    else:
        band = "foundation"
    return RaidScore(global_score=score, weakness=weakness, readiness_band=band)


def choose_plan_length(score: RaidScore) -> RaidPlanLength:
    if score.global_score >= 80:
        return RaidPlanLength.WEEKS_8
    if score.global_score >= 65:
        return RaidPlanLength.WEEKS_12
    if score.global_score >= 45:
        return RaidPlanLength.WEEKS_16
    return RaidPlanLength.WEEKS_24


def phase_for_week(index: int, total: int) -> str:
    ratio = index / total
    if ratio <= 0.50:
        return "base"
    if ratio <= 0.78:
        return "build"
    if ratio <= 0.92:
        return "specific"
    return "taper"


def build_weeks(length: RaidPlanLength, score: RaidScore) -> List[RaidWeek]:
    total = int(length.value.replace("w", ""))
    weeks: List[RaidWeek] = []
    for week in range(1, total + 1):
        phase = phase_for_week(week, total)
        long_session = 75 + week * 5
        if phase == "taper":
            long_session = max(60, int(long_session * 0.65))
        weeks.append(
            RaidWeek(
                week=week,
                focus=phase,
                run_sessions=3 if phase in {"base", "taper"} else 4,
                strength_sessions=2 if phase != "taper" else 1,
                long_session_min=long_session,
                carry_work=score.weakness in {"carry", "endurance"} or phase in {"build", "specific"},
                elevation_focus=score.weakness in {"mountain", "technical"} or phase == "specific",
            )
        )
    return weeks


def build_road_to_raid_plan(profile: RaidProfile) -> RoadToRaidPlan:
    score = compute_raid_score(profile)
    length = choose_plan_length(score)
    weeks = build_weeks(length, score)
    recommendation = f"Priorité {score.weakness}; plan {length.value}; niveau {score.readiness_band}."
    return RoadToRaidPlan(length.value, score, weeks, recommendation)


def serialize_plan(plan: RoadToRaidPlan) -> dict:
    return {
        "plan_length": plan.plan_length,
        "score": asdict(plan.score),
        "weeks": [asdict(w) for w in plan.weeks],
        "recommendation": plan.recommendation,
    }
