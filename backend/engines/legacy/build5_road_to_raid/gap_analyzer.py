
from __future__ import annotations

from .models import RaidProfile, Gap


DEFAULT_TARGETS = {
    "sprint_raid": {
        "endurance": 70,
        "mountain": 65,
        "portage": 60,
        "speed": 65,
        "technical": 60,
        "navigation": 55,
        "recovery": 65,
    },
    "mountain_raid": {
        "endurance": 82,
        "mountain": 85,
        "portage": 78,
        "speed": 65,
        "technical": 75,
        "navigation": 65,
        "recovery": 75,
    },
    "elite_raid": {
        "endurance": 90,
        "mountain": 88,
        "portage": 85,
        "speed": 78,
        "technical": 82,
        "navigation": 75,
        "recovery": 82,
    },
}


class GapAnalyzer:
    """Build 5D — Compare current profile to a RAID target profile."""

    def analyze(self, profile: RaidProfile, target: str = "mountain_raid") -> list[Gap]:
        targets = DEFAULT_TARGETS.get(target, DEFAULT_TARGETS["mountain_raid"])
        gaps: list[Gap] = []
        for domain, target_value in targets.items():
            current = profile.values()[domain]
            gap = round(max(0.0, target_value - current), 1)
            if gap >= 25:
                priority = "critical"
            elif gap >= 15:
                priority = "high"
            elif gap >= 8:
                priority = "medium"
            elif gap > 0:
                priority = "low"
            else:
                priority = "covered"
            gaps.append(
                Gap(
                    domain=domain,
                    current=round(current, 1),
                    target=round(target_value, 1),
                    gap=gap,
                    priority=priority,
                )
            )
        return sorted(gaps, key=lambda g: g.gap, reverse=True)
