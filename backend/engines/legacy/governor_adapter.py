from __future__ import annotations
from governor_engine import SessionGovernor
from governor_models import GovernorInput

class GovernorAdapter:
    def __init__(self) -> None:
        self.governor = SessionGovernor()

    def govern_session(self, data: GovernorInput, planned_duration_min: int) -> dict:
        decision = self.governor.decide(data)
        duration_cap = max(15, int(planned_duration_min * decision.volume_modifier))

        return {
            "decision": decision.decision.value,
            "volume_modifier": decision.volume_modifier,
            "intensity_modifier": decision.intensity_modifier,
            "duration_cap_min": duration_cap,
            "reason_codes": decision.reason_codes,
            "warnings": decision.warnings,
        }
