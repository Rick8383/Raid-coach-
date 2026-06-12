
from __future__ import annotations

from .models import PeriodizationPhase, PlanPhase


class PeriodizationEngine:
    """Build 5E — Split an 8/12/16/24 week RAID plan into phases."""

    def build_phases(self, duration_weeks: int) -> list[PeriodizationPhase]:
        if duration_weeks not in {8, 12, 16, 24}:
            raise ValueError("duration_weeks must be one of 8, 12, 16, 24")

        taper = max(1, round(duration_weeks * 0.12))
        race = 1
        peak = max(2, round(duration_weeks * 0.25))
        build = duration_weeks - taper - race - peak

        return [
            PeriodizationPhase(
                phase=PlanPhase.BUILD,
                weeks=build,
                focus=["aerobic base", "strength endurance", "technical foundations"],
                intensity_factor=0.85,
                volume_factor=1.00,
            ),
            PeriodizationPhase(
                phase=PlanPhase.PEAK,
                weeks=peak,
                focus=["race specificity", "vertical gain", "portage simulation"],
                intensity_factor=1.05,
                volume_factor=1.10,
            ),
            PeriodizationPhase(
                phase=PlanPhase.TAPER,
                weeks=taper,
                focus=["freshness", "sharpness", "load reduction"],
                intensity_factor=0.90,
                volume_factor=0.65,
            ),
            PeriodizationPhase(
                phase=PlanPhase.RACE,
                weeks=race,
                focus=["execution", "recovery", "confidence"],
                intensity_factor=0.75,
                volume_factor=0.40,
            ),
        ]
