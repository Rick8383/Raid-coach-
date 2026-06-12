
from __future__ import annotations

from .models import RaidProfile, Weakness


RECOMMENDATIONS = {
    "endurance": "Add Z2 volume, long trail runs, and aerobic durability blocks.",
    "mountain": "Add uphill tempo, downhill skill, and vertical gain progression.",
    "portage": "Add carries, ruck work, sandbag circuits, and grip endurance.",
    "speed": "Add strides, threshold, short hill reps, and race-pace sharpening.",
    "technical": "Add technical trail practice, obstacle skills, and coordination work.",
    "navigation": "Add map reading, orientation drills, and race simulation.",
    "recovery": "Reduce density, add sleep/recovery targets, and deload when needed.",
}


class WeaknessDetector:
    """Build 5C — Detect limiting RAID domains."""

    def detect(self, profile: RaidProfile, threshold: float = 65.0) -> list[Weakness]:
        weaknesses: list[Weakness] = []
        for domain, score in profile.values().items():
            if score < threshold:
                if score < 40:
                    severity = "critical"
                elif score < 55:
                    severity = "high"
                else:
                    severity = "moderate"
                weaknesses.append(
                    Weakness(
                        domain=domain,
                        score=round(score, 1),
                        severity=severity,
                        recommendation=RECOMMENDATIONS[domain],
                    )
                )
        return sorted(weaknesses, key=lambda w: w.score)
