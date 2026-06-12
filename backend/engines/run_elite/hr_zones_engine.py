from __future__ import annotations
from .models import HRProfile, HRZone, HRZoneRange

_ZONE_DEFS = [
    # zone, pct_min, pct_max, description
    (HRZone.Z1, 0.50, 0.60, "Récupération active — très facile"),
    (HRZone.Z2, 0.60, 0.75, "Endurance fondamentale — conversation possible"),
    (HRZone.Z3, 0.75, 0.85, "Tempo — soutenu mais contrôlé"),
    (HRZone.Z4, 0.85, 0.92, "Seuil — dur, phrases courtes"),
    (HRZone.Z5, 0.92, 1.00, "VO2max / VMA — très dur, non soutenable"),
]


class HRZonesEngine:
    @staticmethod
    def fcmax_tanaka(age: int) -> int:
        if not 14 <= age <= 80:
            raise ValueError("age out of bounds")
        return round(208 - 0.7 * age)

    def compute(self, fc_max: int, fc_rest: int | None = None) -> HRProfile:
        zones: list[HRZoneRange] = []
        if fc_rest is not None:
            # Karvonen: target = rest + pct * (max - rest)
            reserve = fc_max - fc_rest
            for zone, lo, hi, desc in _ZONE_DEFS:
                zones.append(HRZoneRange(
                    zone, round(fc_rest + lo * reserve), round(fc_rest + hi * reserve),
                    lo, hi, desc))
            profile = HRProfile(fc_max, fc_rest, "karvonen", zones)
        else:
            for zone, lo, hi, desc in _ZONE_DEFS:
                zones.append(HRZoneRange(zone, round(lo * fc_max), round(hi * fc_max),
                                         lo, hi, desc))
            profile = HRProfile(fc_max, None, "pct_max", zones)
        profile.validate()
        return profile

    @staticmethod
    def zone_for_bpm(profile: HRProfile, bpm: int) -> HRZone:
        for zr in profile.zones:
            if zr.min_bpm <= bpm <= zr.max_bpm:
                return zr.zone
        return HRZone.Z1 if bpm < profile.zones[0].min_bpm else HRZone.Z5
