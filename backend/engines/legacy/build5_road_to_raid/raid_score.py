
from __future__ import annotations

from .models import RaidProfile, RaidScoreResult, RaidLevel


WEIGHTS = {
    "endurance": 0.24,
    "mountain": 0.20,
    "portage": 0.18,
    "speed": 0.12,
    "technical": 0.12,
    "navigation": 0.08,
    "recovery": 0.06,
}


def classify_score(score: float) -> tuple[RaidLevel, str]:
    if score >= 90:
        return RaidLevel.ELITE, "Elite RAID ready"
    if score >= 78:
        return RaidLevel.ADVANCED, "Advanced RAID profile"
    if score >= 65:
        return RaidLevel.COMPETITIVE, "Competitive but improvable"
    if score >= 50:
        return RaidLevel.DEVELOPING, "Developing RAID base"
    return RaidLevel.BEGINNER, "Foundation required"


class RaidScoreEngine:
    """Build 5B — Produce a weighted RAID score and classification."""

    def compute(self, profile: RaidProfile) -> RaidScoreResult:
        values = profile.values()
        components = {k: round(values[k] * WEIGHTS[k], 2) for k in WEIGHTS}
        score = round(sum(components.values()), 1)
        level, classification = classify_score(score)
        return RaidScoreResult(
            score=score,
            level=level,
            classification=classification,
            components=components,
        )
