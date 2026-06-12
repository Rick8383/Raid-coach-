from __future__ import annotations
from adaptive_models import AthleteContext
from adaptive_programming_engine import AdaptiveProgrammingEngine

class AdaptiveSessionRouter:
    def __init__(self) -> None:
        self.engine = AdaptiveProgrammingEngine()

    def route(self, context: AthleteContext) -> dict:
        adaptation = self.engine.adapt(context)

        return {
            "sport": context.sport,
            "goal": context.goal,
            "decision": adaptation.decision.value,
            "preferred_level": adaptation.preferred_level,
            "duration_cap_min": adaptation.duration_cap_min,
            "volume_factor": adaptation.volume_factor,
            "intensity_factor": adaptation.intensity_factor,
            "reason_codes": adaptation.reason_codes,
            "warnings": adaptation.warnings,
        }
