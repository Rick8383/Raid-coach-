from __future__ import annotations
from recovery_engine import RecoveryEngine
from recovery_models import RecoveryInput

class RecoveryAdapter:
    def __init__(self) -> None:
        self.engine = RecoveryEngine()

    def adapt_training_day(self, data: RecoveryInput, planned_duration_min: int) -> dict:
        recovery = self.engine.evaluate(data)
        duration_cap = max(15, int(planned_duration_min * recovery.volume_factor))

        return {
            "recovery_score": recovery.recovery_score,
            "state": recovery.state.value,
            "recommendation": recovery.recommendation.value,
            "volume_factor": recovery.volume_factor,
            "intensity_factor": recovery.intensity_factor,
            "duration_cap_min": duration_cap,
            "reason_codes": recovery.reason_codes,
            "warnings": recovery.warnings,
        }
