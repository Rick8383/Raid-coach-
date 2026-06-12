from __future__ import annotations
from .models import (HRZone, PaceTable, PaceTarget, PredictionReport,
                     RacePrediction, TerrainType)

_RIEGEL_EXP = 1.06
_STANDARD_DISTANCES = [
    (5.0, "5 km"), (10.0, "10 km"), (15.0, "15 km"),
    (21.0975, "Semi-marathon"), (42.195, "Marathon"),
]


class RunPredictionsEngine:
    """Riegel model: T2 = T1 * (D2/D1)^1.06"""

    def predict(self, distance_km: float, time_sec: int) -> PredictionReport:
        if not 1 <= distance_km <= 100:
            raise ValueError("distance out of bounds")
        if not 180 <= time_sec <= 60000:
            raise ValueError("time out of bounds")
        preds: list[RacePrediction] = []
        for d, label in _STANDARD_DISTANCES:
            t2 = round(time_sec * (d / distance_km) ** _RIEGEL_EXP)
            preds.append(RacePrediction(d, label, t2, round(t2 / d)))
        vma = self.estimate_vma(distance_km, time_sec)
        cooper = self.estimate_cooper(vma)
        return PredictionReport(distance_km, time_sec, vma, cooper, preds)

    @staticmethod
    def estimate_vma(distance_km: float, time_sec: int) -> float:
        """Estimate VMA from a race effort. Sustainable %VMA depends on duration:
        ~6 min -> 100%, 12 min (Cooper) -> ~95%, 30 min -> ~90%, 60 min -> ~85%."""
        speed_kmh = distance_km / (time_sec / 3600)
        minutes = time_sec / 60
        if minutes <= 6:
            pct = 1.00
        elif minutes <= 12:
            pct = 1.00 - 0.05 * (minutes - 6) / 6
        elif minutes <= 30:
            pct = 0.95 - 0.05 * (minutes - 12) / 18
        elif minutes <= 60:
            pct = 0.90 - 0.05 * (minutes - 30) / 30
        else:
            pct = 0.85 - 0.05 * min((minutes - 60) / 60, 1.5)
        return round(speed_kmh / pct, 1)

    @staticmethod
    def estimate_cooper(vma_kmh: float) -> int:
        """Cooper distance ≈ 95% VMA held for 12 min."""
        return round(vma_kmh * 0.95 * 1000 / 5)

    @staticmethod
    def vma_for_cooper_target(target_m: int) -> float:
        """Inverse: VMA needed for a Cooper target."""
        return round(target_m * 5 / 1000 / 0.95, 1)


# %VMA by zone (flat road reference)
_ZONE_PCT_VMA = {
    HRZone.Z1: (0.55, 0.65),
    HRZone.Z2: (0.65, 0.75),
    HRZone.Z3: (0.78, 0.85),
    HRZone.Z4: (0.85, 0.92),
    HRZone.Z5: (0.95, 1.05),
}

_TERRAIN_FACTOR = {
    TerrainType.TRACK: 1.00,
    TerrainType.ROAD: 1.01,
    TerrainType.TRAIL: 1.10,
    TerrainType.HILLY: 1.15,
    TerrainType.MOUNTAIN: 1.30,
    TerrainType.MIXED: 1.08,
}


class PaceCalculatorElite:
    """Target paces per zone, corrected for terrain, elevation (Naismith-like:
    +6 sec/km per 10 m/km of gain) and load carried (+2%/kg above 5 kg)."""

    def table(self, vma_kmh: float, terrain: TerrainType = TerrainType.ROAD,
              elevation_gain_m_per_km: float = 0.0, load_kg: float = 0.0) -> PaceTable:
        if not 8 <= vma_kmh <= 26:
            raise ValueError("vma out of bounds")
        if elevation_gain_m_per_km < 0 or elevation_gain_m_per_km > 200:
            raise ValueError("elevation out of bounds")
        if load_kg < 0 or load_kg > 40:
            raise ValueError("load out of bounds")
        targets: list[PaceTarget] = []
        terr = _TERRAIN_FACTOR[terrain]
        elev_penalty = 6.0 * (elevation_gain_m_per_km / 10.0)  # sec/km
        load_factor = 1 + max(0.0, load_kg - 5) * 0.02
        for zone, (lo, hi) in _ZONE_PCT_VMA.items():
            fast = round((3600 / (vma_kmh * hi)) * terr * load_factor + elev_penalty)
            slow = round((3600 / (vma_kmh * lo)) * terr * load_factor + elev_penalty)
            targets.append(PaceTarget(zone, fast, slow, terrain,
                                      f"+{round(elev_penalty)}s/km D+" if elev_penalty else ""))
        table = PaceTable(vma_kmh, terrain, elevation_gain_m_per_km, load_kg, targets)
        table.validate()
        return table

    @staticmethod
    def fmt(sec_per_km: int) -> str:
        return f"{sec_per_km // 60}:{sec_per_km % 60:02d}/km"
