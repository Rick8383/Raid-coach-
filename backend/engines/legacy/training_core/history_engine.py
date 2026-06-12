from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class WorkoutHistory:
    workout_id: str
    category: str
    family_id: str
    movements: list[str]
    pattern_tags: list[str]
    completed_at: datetime


@dataclass(slots=True, frozen=True)
class HistoryScore:
    score: float
    rejected: bool
    reason: str | None = None


MOVEMENT_WINDOW = 5
PATTERN_WINDOW = 4
FAMILY_WINDOW = 3


class HistoryEngine:
    def score_candidate(
        self,
        workout_id: str,
        family_id: str,
        movements: list[str],
        pattern_tags: list[str],
        history: list[WorkoutHistory],
    ) -> HistoryScore:
        score = 1.0

        if any(item.workout_id == workout_id for item in history):
            return HistoryScore(score=0.0, rejected=True, reason="same_workout")

        recent_families = history[:FAMILY_WINDOW]
        if any(item.family_id == family_id for item in recent_families):
            score *= 0.65

        recent_movements = history[:MOVEMENT_WINDOW]
        previous_movements = {
            movement
            for item in recent_movements
            for movement in item.movements
        }
        movement_overlap = set(movements).intersection(previous_movements)

        if movement_overlap:
            score *= max(0.25, 1.0 - 0.20 * len(movement_overlap))

        recent_patterns = history[:PATTERN_WINDOW]
        previous_patterns = {
            tag
            for item in recent_patterns
            for tag in item.pattern_tags
        }
        pattern_overlap = set(pattern_tags).intersection(previous_patterns)

        if pattern_overlap:
            score *= max(0.40, 1.0 - 0.15 * len(pattern_overlap))

        return HistoryScore(
            score=round(score, 3),
            rejected=False,
            reason=None,
        )
