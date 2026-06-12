from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List


class RaidLevel(str, Enum):
    FOUNDATION = "foundation"
    BASE = "base"
    BUILD = "build"
    READY = "ready"


class RaidWeakness(str, Enum):
    ENDURANCE = "endurance"
    MOUNTAIN = "mountain"
    CARRY = "carry"
    SPEED = "speed"
    TECHNICAL = "technical"


@dataclass(slots=True)
class RaidProfileInput:
    endurance: int
    mountain: int
    carry: int
    speed: int
    technical: int
    available_weeks: int = 16


@dataclass(slots=True)
class RaidProfileResult:
    global_score: int
    level: RaidLevel
    primary_weakness: RaidWeakness
    secondary_weakness: RaidWeakness
    normalized_scores: Dict[str, int]
    recommendation: str


WEIGHTS = {
    RaidWeakness.ENDURANCE.value: 0.30,
    RaidWeakness.MOUNTAIN.value: 0.25,
    RaidWeakness.CARRY.value: 0.20,
    RaidWeakness.SPEED.value: 0.15,
    RaidWeakness.TECHNICAL.value: 0.10,
}


def clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def normalize_profile(profile: RaidProfileInput) -> Dict[str, int]:
    return {
        RaidWeakness.ENDURANCE.value: clamp_score(profile.endurance),
        RaidWeakness.MOUNTAIN.value: clamp_score(profile.mountain),
        RaidWeakness.CARRY.value: clamp_score(profile.carry),
        RaidWeakness.SPEED.value: clamp_score(profile.speed),
        RaidWeakness.TECHNICAL.value: clamp_score(profile.technical),
    }


def compute_global_score(scores: Dict[str, int]) -> int:
    return clamp_score(sum(scores[key] * WEIGHTS[key] for key in WEIGHTS))


def classify_level(global_score: int) -> RaidLevel:
    if global_score >= 80:
        return RaidLevel.READY
    if global_score >= 65:
        return RaidLevel.BUILD
    if global_score >= 45:
        return RaidLevel.BASE
    return RaidLevel.FOUNDATION


def detect_weaknesses(scores: Dict[str, int]) -> tuple[RaidWeakness, RaidWeakness]:
    ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]))
    return RaidWeakness(ordered[0][0]), RaidWeakness(ordered[1][0])


def build_recommendation(result: RaidProfileResult) -> str:
    if result.level == RaidLevel.READY:
        base = "Athlète prêt pour une préparation spécifique courte."
    elif result.level == RaidLevel.BUILD:
        base = "Base solide; priorité au spécifique RAID."
    elif result.level == RaidLevel.BASE:
        base = "Base à construire avant le pic spécifique."
    else:
        base = "Fondation prioritaire avant plan RAID agressif."
    return f"{base} Priorité: {result.primary_weakness.value}; secondaire: {result.secondary_weakness.value}."


class RaidProfiler:
    def evaluate(self, profile: RaidProfileInput) -> RaidProfileResult:
        scores = normalize_profile(profile)
        global_score = compute_global_score(scores)
        level = classify_level(global_score)
        primary, secondary = detect_weaknesses(scores)
        provisional = RaidProfileResult(
            global_score=global_score,
            level=level,
            primary_weakness=primary,
            secondary_weakness=secondary,
            normalized_scores=scores,
            recommendation="",
        )
        provisional.recommendation = build_recommendation(provisional)
        return provisional


def serialize_result(result: RaidProfileResult) -> dict:
    data = asdict(result)
    data["level"] = result.level.value
    data["primary_weakness"] = result.primary_weakness.value
    data["secondary_weakness"] = result.secondary_weakness.value
    return data
