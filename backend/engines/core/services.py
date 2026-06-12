"""BUILD 1 — Core Services
Implémentation réelle des moteurs de règles Build 1 conformes aux specs V9.
"""
from __future__ import annotations
from .models import (DailyMetrics, FatigueZone, PerformanceSnapshot,
                     RaidProfile, ReadinessZone)


# ===== READINESS ENGINE (Build 1.5 spec) =====

class ReadinessEngine:
    """Spécification officielle V9 : 5 facteurs pondérés."""

    WEIGHTS = dict(sleep=0.20, fatigue=0.25, stress=0.15,
                   motivation=0.15, recovery=0.25)

    def score(self, metrics: DailyMetrics) -> float:
        metrics.validate()
        # fatigue/stress : scores invertis (100 - x = meilleur si x bas)
        return round(
            metrics.sleep_quality   * self.WEIGHTS["sleep"]      +
            (100 - metrics.fatigue) * self.WEIGHTS["fatigue"]    +
            (100 - metrics.stress)  * self.WEIGHTS["stress"]     +
            metrics.motivation      * self.WEIGHTS["motivation"] +
            metrics.recovery        * self.WEIGHTS["recovery"],
            1)

    @staticmethod
    def zone(score: float) -> ReadinessZone:
        if score >= 90: return ReadinessZone.PEAK
        if score >= 75: return ReadinessZone.GREEN
        if score >= 60: return ReadinessZone.YELLOW
        if score >= 40: return ReadinessZone.ORANGE
        return ReadinessZone.RED

    def evaluate(self, metrics: DailyMetrics) -> tuple[float, ReadinessZone]:
        s = self.score(metrics)
        metrics.readiness_score = s
        return s, self.zone(s)


# ===== FATIGUE ENGINE (Build 1.6 spec) =====

class FatigueEngine:
    """ACWR (Acute:Chronic Workload Ratio) — fenêtres 7j / 42j."""

    @staticmethod
    def acwr(acute_7d: float, chronic_42d: float) -> float:
        if chronic_42d <= 0:
            return 1.0
        return round(acute_7d / chronic_42d, 2)

    @staticmethod
    def zone(ratio: float) -> FatigueZone:
        if ratio <= 1.2: return FatigueZone.OPTIMAL
        if ratio <= 1.4: return FatigueZone.WARNING
        return FatigueZone.DANGER

    def evaluate(self, acute_7d: float, chronic_42d: float
                 ) -> tuple[float, FatigueZone]:
        r = self.acwr(acute_7d, chronic_42d)
        return r, self.zone(r)


# ===== RAID PROFILE ENGINE =====

class RaidProfileEngine:
    """Calcule et met à jour le profil RAID depuis un snapshot."""

    def build_from_snapshot(self, snap: PerformanceSnapshot,
                            carry_result: float = 50.0,
                            mountain_result: float = 50.0) -> RaidProfile:
        snap.validate()
        # Endurance : basé sur Cooper ou vma
        cooper = snap.cooper_m or 2500
        endurance = round(min(100, (cooper - 2000) / (3500 - 2000) * 100), 1)
        # Force : raid_score
        strength = round(min(100, snap.raid_score), 1)
        profile = RaidProfile(
            athlete_id=snap.athlete_id,
            endurance_score=max(0.0, endurance),
            mountain_score=min(100.0, max(0.0, mountain_result)),
            carry_score=min(100.0, max(0.0, carry_result)),
            strength_score=max(0.0, strength),
            resilience_score=min(100.0, max(0.0, snap.readiness_score * 0.8)),
        )
        profile.validate()
        return profile
