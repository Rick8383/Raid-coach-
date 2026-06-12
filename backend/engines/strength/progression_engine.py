from __future__ import annotations
from .models import (AdaptiveLoadInput, AdaptiveLoadOutput, LoadDecision,
                     ProgressionPhase)


class LongTermProgressionEngine:
    """Decides the strength phase from week position and context."""

    PHASE_CYCLE = [
        (ProgressionPhase.ACCUMULATION, 3),
        (ProgressionPhase.INTENSIFICATION, 2),
        (ProgressionPhase.DELOAD, 1),
    ]
    CYCLE_LEN = 6

    def phase_for_week(self, week_in_block: int, weeks_to_goal: int | None = None) -> ProgressionPhase:
        if week_in_block < 0:
            raise ValueError("week_in_block must be >= 0")
        if weeks_to_goal is not None:
            if weeks_to_goal <= 1:
                return ProgressionPhase.TEST
            if weeks_to_goal <= 3:
                return ProgressionPhase.PEAKING
        pos = week_in_block % self.CYCLE_LEN
        acc = 0
        for phase, length in self.PHASE_CYCLE:
            acc += length
            if pos < acc:
                return phase
        return ProgressionPhase.ACCUMULATION

    @staticmethod
    def level_for_phase(phase: ProgressionPhase, athlete_level: str = "intermediate") -> str:
        mapping = {
            ProgressionPhase.ACCUMULATION: athlete_level,
            ProgressionPhase.INTENSIFICATION: "advanced" if athlete_level != "beginner" else "intermediate",
            ProgressionPhase.PEAKING: "peaking",
            ProgressionPhase.TEST: "peaking",
            ProgressionPhase.DELOAD: "deload",
        }
        return mapping[phase]


class AdaptiveLoadEngine:
    """Daily strength load arbitration. Safety first: never a dangerous session."""

    def decide(self, data: AdaptiveLoadInput) -> AdaptiveLoadOutput:
        data.validate()
        reasons: list[str] = []
        warnings: list[str] = []

        if data.pain_flag:
            reasons.append("pain_override")
            warnings.append("avoid_painful_patterns")
            out = AdaptiveLoadOutput(LoadDecision.TECHNIQUE, 0.50, 0.55, reasons, warnings)
            out.validate()
            return out

        if data.recovery_score < 35 or data.sleep_quality < 30:
            reasons.append("critical_recovery")
            warnings.append("active_recovery_recommended")
            out = AdaptiveLoadOutput(LoadDecision.DELOAD, 0.40, 0.50, reasons, warnings)
            out.validate()
            return out

        total_load = data.run_load_7d + data.crossfit_load_7d + data.strength_load_7d
        if total_load > 220 or data.sessions_since_deload >= 16:
            reasons.append("accumulated_load_high" if total_load > 220 else "deload_overdue")
            out = AdaptiveLoadOutput(LoadDecision.REDUCE, 0.70, 0.80, reasons,
                                     ["plan_deload_week"])
            out.validate()
            return out

        if data.hrv_trend == "down" and data.recovery_score < 60:
            reasons.append("hrv_decline")
            out = AdaptiveLoadOutput(LoadDecision.MAINTAIN, 0.90, 0.90, reasons,
                                     ["monitor_hrv"])
            out.validate()
            return out

        if data.recovery_score >= 80 and data.sleep_quality >= 70 and total_load <= 150:
            reasons.append("green_light_progress")
            out = AdaptiveLoadOutput(LoadDecision.INCREASE, 1.08, 1.05, reasons, [])
            out.validate()
            return out

        reasons.append("standard_conditions")
        out = AdaptiveLoadOutput(LoadDecision.MAINTAIN, 1.0, 1.0, reasons, [])
        out.validate()
        return out
