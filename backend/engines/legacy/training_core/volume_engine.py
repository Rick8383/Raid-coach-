from __future__ import annotations

from dataclasses import dataclass

from .progression_engine import ProgressionState
from .training_context import TrainingContext


@dataclass(slots=True, frozen=True)
class VolumePlan:
    volume_factor: float
    intensity_factor: float
    frequency_factor: float


class VolumeEngine:
    def compute(
        self,
        context: TrainingContext,
        progression_state: ProgressionState,
    ) -> VolumePlan:
        context.validate()

        if progression_state == ProgressionState.PROGRESS:
            return VolumePlan(
                volume_factor=1.10,
                intensity_factor=1.05,
                frequency_factor=1.00,
            )

        if progression_state == ProgressionState.MAINTAIN:
            return VolumePlan(
                volume_factor=1.00,
                intensity_factor=1.00,
                frequency_factor=1.00,
            )

        if progression_state == ProgressionState.DELOAD:
            return VolumePlan(
                volume_factor=0.80,
                intensity_factor=0.90,
                frequency_factor=0.90,
            )

        return VolumePlan(
            volume_factor=0.60,
            intensity_factor=0.70,
            frequency_factor=0.75,
        )
