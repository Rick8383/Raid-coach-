from __future__ import annotations
from recovery_models import RecoveryInput, RecoveryOutput, RecoveryRecommendation, RecoveryState

class RecoveryEngine:
    def evaluate(self, data: RecoveryInput) -> RecoveryOutput:
        data.validate()

        score = 100
        reasons: list[str] = []
        warnings: list[str] = []

        if data.sleep_hours < 5:
            score -= 25
            reasons.append("sleep_debt_critical")
        elif data.sleep_hours < 6.5:
            score -= 12
            reasons.append("sleep_debt_moderate")

        score -= int((100 - data.sleep_quality) * 0.12)
        score -= int(data.fatigue_score * 0.20)
        score -= int(data.soreness_score * 0.14)
        score -= int(data.stress_score * 0.12)
        score -= int(data.last_training_load * 0.10)

        if data.days_since_rest >= 8:
            score -= 14
            reasons.append("rest_day_overdue")
        elif data.days_since_rest >= 5:
            score -= 7
            reasons.append("rest_day_due_soon")

        if data.hydration_score < 50:
            score -= 6
            reasons.append("hydration_low")

        if data.nutrition_score < 50:
            score -= 6
            reasons.append("nutrition_low")

        if data.pain_flags:
            score -= 25
            reasons.append("pain_flag")
            warnings.append("pain_guardrail")

        score = max(0, min(100, score))
        state = self._state(score, bool(data.pain_flags))
        recommendation = self._recommendation(state)
        volume_factor, intensity_factor = self._factors(state)

        output = RecoveryOutput(
            recovery_score=score,
            state=state,
            recommendation=recommendation,
            volume_factor=volume_factor,
            intensity_factor=intensity_factor,
            reason_codes=reasons or ["recovery_normal"],
            warnings=warnings,
        )
        output.validate()
        return output

    def _state(self, score: int, pain: bool) -> RecoveryState:
        if pain or score < 35:
            return RecoveryState.CRITICAL
        if score < 50:
            return RecoveryState.POOR
        if score < 70:
            return RecoveryState.MODERATE
        if score < 85:
            return RecoveryState.GOOD
        return RecoveryState.OPTIMAL

    def _recommendation(self, state: RecoveryState) -> RecoveryRecommendation:
        if state == RecoveryState.OPTIMAL:
            return RecoveryRecommendation.HIGH_INTENSITY_ALLOWED
        if state == RecoveryState.GOOD:
            return RecoveryRecommendation.NORMAL_TRAINING
        if state == RecoveryState.MODERATE:
            return RecoveryRecommendation.REDUCE_VOLUME
        if state == RecoveryState.POOR:
            return RecoveryRecommendation.ACTIVE_RECOVERY
        return RecoveryRecommendation.REST_DAY

    def _factors(self, state: RecoveryState) -> tuple[float, float]:
        if state == RecoveryState.OPTIMAL:
            return 1.08, 1.05
        if state == RecoveryState.GOOD:
            return 1.00, 1.00
        if state == RecoveryState.MODERATE:
            return 0.80, 0.85
        if state == RecoveryState.POOR:
            return 0.55, 0.65
        return 0.30, 0.40
