"""Réglages athlète pour les générateurs (allures, FC, charge).

Constantes par défaut (surchargées par le profil réel si fourni) :
VMA 14 km/h, FCmax 186 (Tanaka), poids 75 kg, sciatique L5-S1 active.
"""
from __future__ import annotations

VMA_ATHLETE = 14.0      # km/h
FCMAX = 186             # bpm
WEIGHT_KG = 75.0
NO_LUMBAR_HEAVY_IN_FATIGUE = True   # règle sciatique globale, ON par défaut


def speed_kmh(pct_vma: float, vma: float = VMA_ATHLETE) -> float:
    return round(vma * pct_vma / 100, 1)


def pace_min_km(speed: float) -> str:
    """Allure mm:ss/km depuis une vitesse km/h."""
    total = round(3600 / speed)
    return f"{total // 60}:{total % 60:02d}"


def pace_from_pct(pct_vma: float, vma: float = VMA_ATHLETE) -> tuple[float, str]:
    s = speed_kmh(pct_vma, vma)
    return s, pace_min_km(s)


def fc_bpm(pct_fcmax: float, fcmax: int = FCMAX) -> int:
    return round(fcmax * pct_fcmax / 100)
