from __future__ import annotations
from readiness_models import DailyReadinessInput, ReadinessDecision, ReadinessOutput

class ReadinessEngine:
    def evaluate(self, data: DailyReadinessInput) -> ReadinessOutput:
        data.validate()

        reasons: list[str] = []
        warnings: list[str] = []

        score = 100

        if data.sleep_hours < 5:
            score -= 25
            reasons.append("very_low_sleep")
        elif data.sleep_hours < 6.5:
            score -= 12
            reasons.append("low_sleep")

        score -= int((100 - data.sleep_quality) * 0.12)
        score -= int(data.fatigue * 0.18)
        score -= int(data.soreness * 0.12)
        score -= int(data.stress * 0.10)
        score -= int(data.recent_load * 0.08)
        score -= int(max(0, data.recent_rpe - 6) * 4)

        if data.motivation < 35:
            score -= 8
            reasons.append("low_motivation")

        if data.hrv_status == "low":
            score -= 12
            reasons.append("low_hrv")
        elif data.hrv_status == "high":
            score += 4
            reasons.append("high_hrv")

        if data.resting_hr_delta >= 8:
            score -= 10
            reasons.append("resting_hr_elevated")

        if data.pain_flags:
            score -= 20
            reasons.append("pain_flag")
            warnings.append("pain_guardrail")

        score = max(0, min(100, score))

        decision = self._decision_from_score(score, data)
        volume, intensity, duration = self._factors(decision)

        output = ReadinessOutput(
            score=score,
            decision=decision,
            volume_factor=volume,
            intensity_factor=intensity,
            duration_cap_factor=duration,
            reason_codes=reasons or ["normal_readiness"],
            warnings=warnings,
        )
        output.validate()
        return output

    def _decision_from_score(self, score: int, data: DailyReadinessInput) -> ReadinessDecision:
        if data.pain_flags or score < 35:
            return ReadinessDecision.RED
        if score < 50:
            return ReadinessDecision.ORANGE
        if score < 65:
            return ReadinessDecision.YELLOW
        if score < 80:
            return ReadinessDecision.MAINTAIN
        return ReadinessDecision.GREEN

    def _factors(self, decision: ReadinessDecision) -> tuple[float, float, float]:
        if decision == ReadinessDecision.RED:
            return 0.35, 0.45, 0.50
        if decision == ReadinessDecision.ORANGE:
            return 0.55, 0.65, 0.70
        if decision == ReadinessDecision.YELLOW:
            return 0.75, 0.85, 0.85
        if decision == ReadinessDecision.MAINTAIN:
            return 1.00, 1.00, 1.00
        return 1.08, 1.05, 1.00
