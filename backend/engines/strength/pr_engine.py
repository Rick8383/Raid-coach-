from __future__ import annotations
from .models import PREstimate, PRRecord


class PREngine:
    """e1RM estimation and rep-max projections (Epley + Brzycki average)."""

    @staticmethod
    def e1rm(weight_kg: float, reps: int) -> float:
        if reps <= 0:
            raise ValueError("reps must be > 0")
        if reps == 1:
            return round(weight_kg, 1)
        epley = weight_kg * (1 + reps / 30)
        if reps > 12:
            # Brzycki diverge au-delà de ~12 reps (singularité à 37) :
            # les séries longues (tractions, pompes...) utilisent Epley seul
            return round(epley, 1)
        brzycki = weight_kg * 36 / (37 - reps)
        return round((epley + brzycki) / 2, 1)

    @staticmethod
    def rm_at(e1rm: float, reps: int) -> float:
        """Inverse Epley: weight for a target rep count."""
        return round(e1rm / (1 + reps / 30), 1)

    def estimate(self, record: PRRecord) -> PREstimate:
        record.validate()
        e1 = self.e1rm(record.weight_kg, record.reps)
        return PREstimate(
            movement_id=record.movement_id,
            e1rm=e1,
            rm3=self.rm_at(e1, 3),
            rm5=self.rm_at(e1, 5),
            rm8=self.rm_at(e1, 8),
            source_weight=record.weight_kg,
            source_reps=record.reps,
        )

    @staticmethod
    def progression_delta(history: list[PRRecord]) -> float:
        """e1RM delta between oldest and newest record (kg)."""
        if len(history) < 2:
            return 0.0
        ordered = sorted(history, key=lambda r: r.date)
        first = PREngine.e1rm(ordered[0].weight_kg, ordered[0].reps)
        last = PREngine.e1rm(ordered[-1].weight_kg, ordered[-1].reps)
        return round(last - first, 1)

    @staticmethod
    def weeks_to_target(current_e1rm: float, target_e1rm: float,
                        weekly_gain_pct: float = 0.6) -> int:
        """Conservative estimate of weeks to reach a target e1RM.
        weekly_gain_pct: realistic intermediate gain ~0.5-0.8%/week."""
        if current_e1rm <= 0:
            raise ValueError("current_e1rm must be > 0")
        if target_e1rm <= current_e1rm:
            return 0
        weeks = 0
        value = current_e1rm
        while value < target_e1rm and weeks < 520:
            value *= 1 + weekly_gain_pct / 100
            weeks += 1
        return weeks
