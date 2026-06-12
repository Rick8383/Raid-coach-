from __future__ import annotations
from dataclasses import dataclass

from .models import RaidStrengthReport, RaidStrengthTarget
from .pr_engine import PREngine

# Targets calibrated on RAID (police nationale) selection demands:
# présélection = circuit force au poids de corps avec minimas, puis semaine de
# sélection : tractions/pompes/dips/relevés de jambes à épuisement,
# 2 montées de corde 5 m, Cooper 12 min + sprint 50 m, natation/apnée.
# Targets below = "comfortable pass" level (safety margin above estimated minima).

@dataclass(slots=True, frozen=True)
class _Target:
    movement_id: str
    name: str
    target: float
    unit: str
    weight: float  # importance weight in global readiness


RAID_STRENGTH_STANDARDS: list[_Target] = [
    _Target("pullups_max", "Tractions strictes (série max)", 20, "reps", 0.22),
    _Target("pushups_max", "Pompes (série max)", 60, "reps", 0.16),
    _Target("dips_max", "Dips (série max)", 25, "reps", 0.14),
    _Target("leg_raises_max", "Relevés de jambes (série max)", 20, "reps", 0.10),
    _Target("rope_climb_5m", "Montées de corde 5 m consécutives", 2, "reps", 0.16),
    _Target("bench_ratio", "Développé couché (ratio poids de corps)", 1.2, "ratio_bw", 0.08),
    _Target("squat_ratio", "Squat (ratio poids de corps)", 1.5, "ratio_bw", 0.08),
    _Target("cooper_m", "Cooper 12 min (mètres)", 3000, "meters", 0.06),
]



# Elite tier — top 5% of candidates (user-defined targets, 11/06/2026)
RAID_ELITE_TARGETS: list[_Target] = [
    _Target("pullups_max", "Tractions strictes (série max)", 35, "reps", 0.22),
    _Target("pushups_max", "Pompes (série max)", 120, "reps", 0.16),
    _Target("dips_max", "Dips (série max)", 60, "reps", 0.14),
    _Target("leg_raises_max", "Toes to bar (série max)", 80, "reps", 0.10),
    _Target("rope_climb_5m", "Montées de corde 5 m consécutives", 4, "reps", 0.16),
    _Target("bench_ratio", "Développé couché (ratio poids de corps)", 1.4, "ratio_bw", 0.08),
    _Target("squat_ratio", "Squat (ratio poids de corps)", 1.8, "ratio_bw", 0.08),
    _Target("cooper_m", "Cooper 12 min (mètres)", 3200, "meters", 0.06),
]


class RoadToRaidStrength:
    """Gap analysis between current athlete level and RAID strength standards."""

    def analyze(self, current: dict[str, float], bodyweight_kg: float,
                tier: str = "pass") -> RaidStrengthReport:
        """tier: 'pass' = passage confortable | 'elite' = top 5% candidats."""
        if bodyweight_kg <= 30 or bodyweight_kg > 200:
            raise ValueError("bodyweight out of bounds")
        targets: list[RaidStrengthTarget] = []
        weighted_sum = 0.0
        standards = RAID_ELITE_TARGETS if tier == "elite" else RAID_STRENGTH_STANDARDS
        for std in standards:
            raw = current.get(std.movement_id, 0.0)
            value = raw / bodyweight_kg if std.unit == "ratio_bw" and raw > 5 else raw
            ratio = min(value / std.target, 1.0) if std.target > 0 else 0.0
            gap_pct = round((1 - ratio) * 100, 1)
            weighted_sum += ratio * std.weight
            targets.append(RaidStrengthTarget(
                movement_id=std.movement_id, name=std.name,
                target_value=std.target, unit=std.unit,
                current_value=round(value, 2), gap_pct=gap_pct,
                priority=0,
            ))
        # priority = biggest weighted gap first
        ordered = sorted(targets, key=lambda t: t.gap_pct, reverse=True)
        targets = [RaidStrengthTarget(t.movement_id, t.name, t.target_value, t.unit,
                                      t.current_value, t.gap_pct, i + 1)
                   for i, t in enumerate(ordered)]
        readiness = round(weighted_sum * 100, 1)
        primary = targets[0].name if targets else "n/a"
        weeks = self._estimate_weeks(targets)
        rec = self._recommendation(readiness, primary, weeks)
        return RaidStrengthReport(
            targets=targets, global_readiness_pct=readiness,
            primary_focus=primary, estimated_weeks_to_ready=weeks,
            recommendation=rec,
        )

    @staticmethod
    def _estimate_weeks(targets: list[RaidStrengthTarget]) -> int:
        """Bodyweight rep movements: ~1 rep gained / 2-3 weeks of focused work.
        Barbell ratios: ~0.6%/week e1RM. Take the max across gaps."""
        worst = 0
        for t in targets:
            if t.gap_pct <= 0:
                continue
            if t.unit == "reps":
                missing = t.target_value - t.current_value
                worst = max(worst, int(missing * 2.5))
            elif t.unit == "ratio_bw":
                if t.current_value > 0:
                    worst = max(worst, PREngine.weeks_to_target(
                        t.current_value * 100, t.target_value * 100))
                else:
                    worst = max(worst, 52)
            elif t.unit == "meters":
                missing_pct = t.gap_pct
                worst = max(worst, int(missing_pct * 1.2))
        return min(worst, 260)

    @staticmethod
    def _recommendation(readiness: float, primary: str, weeks: int) -> str:
        if readiness >= 90:
            return f"Niveau test atteint. Entretien + marge de sécurité. Focus residuel: {primary}."
        if readiness >= 75:
            return f"Proche du niveau requis (~{weeks} sem. de travail ciblé). Priorité: {primary}."
        if readiness >= 55:
            return f"Base solide, écart réel à combler (~{weeks} sem.). Priorité absolue: {primary}."
        return f"Fondation à construire (~{weeks} sem. minimum). Commencer par: {primary}."
