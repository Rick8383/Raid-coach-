from __future__ import annotations
from adaptive_models import AdaptationDecision, AdaptationOutput, AthleteContext

class AdaptiveProgrammingEngine:
    def adapt(self, context: AthleteContext) -> AdaptationOutput:
        context.validate()

        reasons: list[str] = []
        warnings: list[str] = []

        decision = AdaptationDecision.MAINTAIN
        volume_factor = 1.0
        intensity_factor = 1.0
        duration_cap = context.available_time_min
        preferred_level = "intermediate"

        if context.injury_risk >= 75:
            reasons.append("high_injury_risk")
            warnings.append("injury_risk_guardrail")
            decision = AdaptationDecision.RECOVERY
            volume_factor = 0.45
            intensity_factor = 0.55
            duration_cap = min(duration_cap, 35)
            preferred_level = "deload"

        elif context.readiness < 35 or context.fatigue >= 85:
            reasons.append("low_readiness_or_extreme_fatigue")
            decision = AdaptationDecision.RECOVERY
            volume_factor = 0.55
            intensity_factor = 0.65
            duration_cap = min(duration_cap, 40)
            preferred_level = "deload"

        elif context.readiness < 55 or context.fatigue >= 70:
            reasons.append("fatigue_deload")
            decision = AdaptationDecision.DELOAD
            volume_factor = 0.75
            intensity_factor = 0.85
            duration_cap = min(duration_cap, 50)
            preferred_level = "deload"

        elif context.readiness >= 90 and context.fatigue <= 30 and context.recent_volume <= 65:
            reasons.append("high_readiness_low_fatigue")
            decision = AdaptationDecision.INTENSIFY
            volume_factor = 1.12
            intensity_factor = 1.15
            preferred_level = "advanced"

        elif context.readiness >= 75 and context.fatigue <= 50:
            reasons.append("good_training_window")
            decision = AdaptationDecision.PROGRESS
            volume_factor = 1.08
            intensity_factor = 1.05
            preferred_level = "intermediate"

        else:
            reasons.append("stable_maintenance")
            decision = AdaptationDecision.MAINTAIN
            volume_factor = 1.0
            intensity_factor = 1.0
            preferred_level = "intermediate"

        if context.recent_volume >= 80:
            reasons.append("recent_volume_high")
            volume_factor = min(volume_factor, 0.85)
            duration_cap = min(duration_cap, 55)
            if decision in {AdaptationDecision.PROGRESS, AdaptationDecision.INTENSIFY}:
                decision = AdaptationDecision.MAINTAIN
                preferred_level = "intermediate"

        if context.recent_intensity >= 80:
            reasons.append("recent_intensity_high")
            intensity_factor = min(intensity_factor, 0.9)
            if decision == AdaptationDecision.INTENSIFY:
                decision = AdaptationDecision.PROGRESS

        if context.training_age_months < 6:
            reasons.append("low_training_age")
            volume_factor = min(volume_factor, 0.85)
            intensity_factor = min(intensity_factor, 0.9)
            preferred_level = "beginner" if preferred_level != "deload" else "deload"

        if context.sleep_hours is not None and context.sleep_hours < 6:
            reasons.append("low_sleep")
            volume_factor = min(volume_factor, 0.85)
            intensity_factor = min(intensity_factor, 0.9)

        if context.stress_score is not None and context.stress_score >= 80:
            reasons.append("high_stress")
            volume_factor = min(volume_factor, 0.8)
            duration_cap = min(duration_cap, 45)

        output = AdaptationOutput(
            decision=decision,
            volume_factor=round(volume_factor, 2),
            intensity_factor=round(intensity_factor, 2),
            duration_cap_min=duration_cap,
            preferred_level=preferred_level,
            reason_codes=reasons,
            warnings=warnings,
        )
        output.validate()
        return output
