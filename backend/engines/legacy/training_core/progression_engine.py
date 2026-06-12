from __future__ import annotations

from enum import Enum

from .training_context import TrainingContext


class ProgressionState(str, Enum):
    PROGRESS = "progress"
    MAINTAIN = "maintain"
    DELOAD = "deload"
    RECOVER = "recover"


class ProgressionEngine:
    def compute(self, context: TrainingContext) -> ProgressionState:
        context.validate()

        if context.readiness < 40:
            return ProgressionState.RECOVER

        if context.fatigue > 85:
            return ProgressionState.RECOVER

        if context.readiness < 60:
            return ProgressionState.DELOAD

        if context.fatigue > 70:
            return ProgressionState.DELOAD

        if context.readiness >= 80 and context.fatigue <= 40:
            return ProgressionState.PROGRESS

        return ProgressionState.MAINTAIN
