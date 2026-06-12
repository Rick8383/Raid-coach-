
from __future__ import annotations

from .models import RaidProfile


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, round(float(value), 1)))


class RaidProfiler:
    """Build 5A — Convert raw athlete capabilities into a normalized RAID profile."""

    def create_profile(
        self,
        endurance: float,
        mountain: float,
        portage: float,
        speed: float,
        technical: float,
        navigation: float = 50.0,
        recovery: float = 70.0,
    ) -> RaidProfile:
        return RaidProfile(
            endurance=_clamp(endurance),
            mountain=_clamp(mountain),
            portage=_clamp(portage),
            speed=_clamp(speed),
            technical=_clamp(technical),
            navigation=_clamp(navigation),
            recovery=_clamp(recovery),
        )
