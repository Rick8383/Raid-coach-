from __future__ import annotations
from readiness_engine import ReadinessEngine
from readiness_models import DailyReadinessInput

class ReadinessAdapter:
    def __init__(self) -> None:
        self.engine = ReadinessEngine()

    def adapt_session_request(self, data: DailyReadinessInput, planned_duration_min: int) -> dict:
        readiness = self.engine.evaluate(data)
        duration_cap = max(15, int(planned_duration_min * readiness.duration_cap_factor))

        return {
            "score": readiness.score,
            "decision": readiness.decision.value,
            "volume_factor": readiness.volume_factor,
            "intensity_factor": readiness.intensity_factor,
            "duration_cap_min": duration_cap,
            "reason_codes": readiness.reason_codes,
            "warnings": readiness.warnings,
        }
