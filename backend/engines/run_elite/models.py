from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class HRZone(str, Enum):
    Z1 = "z1_recovery"
    Z2 = "z2_endurance"
    Z3 = "z3_tempo"
    Z4 = "z4_threshold"
    Z5 = "z5_vo2max"


class TerrainType(str, Enum):
    ROAD = "road"
    TRACK = "track"
    TRAIL = "trail"
    HILLY = "hilly"
    MOUNTAIN = "mountain"
    MIXED = "mixed"


@dataclass(slots=True, frozen=True)
class HRZoneRange:
    zone: HRZone
    min_bpm: int
    max_bpm: int
    pct_min: float
    pct_max: float
    description: str


@dataclass(slots=True, frozen=True)
class HRProfile:
    fc_max: int
    fc_rest: int | None
    method: str  # "pct_max" | "karvonen"
    zones: list[HRZoneRange]

    def validate(self) -> None:
        if not 120 <= self.fc_max <= 230:
            raise ValueError("fc_max out of bounds")
        if self.fc_rest is not None and not 30 <= self.fc_rest <= 100:
            raise ValueError("fc_rest out of bounds")
        if len(self.zones) != 5:
            raise ValueError("expected 5 zones")


@dataclass(slots=True, frozen=True)
class RacePrediction:
    distance_km: float
    label: str
    predicted_time_sec: int
    predicted_pace_sec_km: int


@dataclass(slots=True, frozen=True)
class PredictionReport:
    source_distance_km: float
    source_time_sec: int
    vma_estimate_kmh: float
    cooper_estimate_m: int
    predictions: list[RacePrediction]


@dataclass(slots=True, frozen=True)
class PaceTarget:
    zone: HRZone
    pace_min_sec_km: int  # fastest
    pace_max_sec_km: int  # slowest
    terrain: TerrainType
    notes: str = ""


@dataclass(slots=True, frozen=True)
class PaceTable:
    vma_kmh: float
    terrain: TerrainType
    elevation_gain_m_per_km: float
    load_kg: float
    targets: list[PaceTarget]

    def validate(self) -> None:
        if not 8 <= self.vma_kmh <= 26:
            raise ValueError("vma out of bounds")
        if not self.targets:
            raise ValueError("empty pace table")
