from __future__ import annotations
from .models import ArbitrationResult, TrainingGoal

# Urgency weight by proximity (weeks to target)
def _urgency(weeks: int) -> float:
    if weeks <= 2:
        return 1.0
    if weeks <= 6:
        return 0.85
    if weeks <= 12:
        return 0.65
    if weeks <= 26:
        return 0.45
    if weeks <= 52:
        return 0.30
    return 0.20


class GoalArbitrationEngine:
    """When several goals compete, decide the weekly quality-work allocation.
    Score = urgency(weeks) × priority_weight. RAID selection always floors at 30%."""

    RAID_FLOOR_PCT = 30.0

    def arbitrate(self, goals: list[TrainingGoal]) -> ArbitrationResult:
        if not goals:
            raise ValueError("no goals provided")
        scores: dict[str, float] = {}
        rationale: list[str] = []
        for g in goals:
            g.validate()
            prio_w = (6 - g.priority) / 5  # P1 -> 1.0, P5 -> 0.2
            scores[g.goal_id] = round(_urgency(g.target_date_weeks) * prio_w, 3)
        ranked = sorted(goals, key=lambda g: scores[g.goal_id], reverse=True)
        total = sum(scores.values()) or 1.0
        alloc = {g.goal_id: round(scores[g.goal_id] / total * 100, 1) for g in goals}

        # RAID floor: long-horizon main goal never starved by short-term races
        raid_goals = [g for g in goals if "raid" in g.goal_id.lower() or "raid" in g.name.lower()]
        if raid_goals:
            rg = raid_goals[0]
            if alloc[rg.goal_id] < self.RAID_FLOOR_PCT:
                deficit = self.RAID_FLOOR_PCT - alloc[rg.goal_id]
                others = [g for g in goals if g.goal_id != rg.goal_id]
                pool = sum(alloc[g.goal_id] for g in others) or 1.0
                for g in others:
                    alloc[g.goal_id] = round(alloc[g.goal_id] * (1 - deficit / pool), 1)
                alloc[rg.goal_id] = self.RAID_FLOOR_PCT
                rationale.append(f"plancher_raid_{self.RAID_FLOOR_PCT:.0f}pct_applique")

        primary = ranked[0]
        rationale.append(f"primaire={primary.name} (urgence {primary.target_date_weeks} sem, P{primary.priority})")
        if len(ranked) > 1:
            rationale.append(f"secondaire={ranked[1].name}")
        return ArbitrationResult(
            primary_goal_id=primary.goal_id,
            ranked_goal_ids=[g.goal_id for g in ranked],
            allocation_pct=alloc,
            rationale=rationale,
        )
