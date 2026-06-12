from __future__ import annotations
from governor_models import GovernorDecision, GovernorInput, GovernorOutput

class SessionGovernor:
    def decide(self, data: GovernorInput) -> GovernorOutput:
        data.validate()

        reasons: list[str] = []
        warnings: list[str] = []

        if data.pain_flag:
            reasons.append("pain_override")
            warnings.append("movement_modification_required")
            output = GovernorOutput(
                decision=GovernorDecision.MODIFY,
                volume_modifier=0.70,
                intensity_modifier=0.75,
                reason_codes=reasons,
                warnings=warnings,
            )
            output.validate()
            return output

        if data.readiness_score < 35 or data.recovery_score < 35:
            reasons.append("readiness_or_recovery_critical")
            output = GovernorOutput(
                decision=GovernorDecision.BLOCK,
                volume_modifier=0.30,
                intensity_modifier=0.40,
                reason_codes=reasons,
                warnings=["recovery_day_recommended"],
            )
            output.validate()
            return output

        if data.high_risk_movement and (data.readiness_score < 70 or data.recovery_score < 70):
            reasons.append("high_risk_movement_modified")
            output = GovernorOutput(
                decision=GovernorDecision.MODIFY,
                volume_modifier=0.75,
                intensity_modifier=0.80,
                reason_codes=reasons,
                warnings=["remove_high_risk_movements"],
            )
            output.validate()
            return output

        if data.readiness_score >= 85 and data.recovery_score >= 85 and data.recent_load <= 70:
            reasons.append("green_light")
            output = GovernorOutput(
                decision=GovernorDecision.ALLOW,
                volume_modifier=1.00,
                intensity_modifier=1.00,
                reason_codes=reasons,
            )
            output.validate()
            return output

        if data.recent_load >= 85:
            reasons.append("recent_load_high")
            output = GovernorOutput(
                decision=GovernorDecision.REDUCE,
                volume_modifier=0.75,
                intensity_modifier=0.85,
                reason_codes=reasons,
            )
            output.validate()
            return output

        reasons.append("moderate_readiness_or_recovery")
        output = GovernorOutput(
            decision=GovernorDecision.REDUCE,
            volume_modifier=0.80,
            intensity_modifier=0.85,
            reason_codes=reasons,
        )
        output.validate()
        return output
