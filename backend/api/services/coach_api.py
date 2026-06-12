"""API service layer — pure Python orchestration of all engines.
This layer is framework-free: FastAPI routers are thin wrappers around it.
Everything here is fully testable without FastAPI installed."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engines" / "legacy"))

from engines.coach_brain import (DailyContext, DailyDecisionEngine,  # noqa: E402
                                 Discipline, FatigueBudgetEngine,
                                 GoalArbitrationEngine, SessionLoad,
                                 TrainingGoal, WeekType)
from engines.nutrition import (ActivityLevel, NutritionPhase,  # noqa: E402
                               NutritionProfile, NutritionService)
from engines.run_elite import (HRZonesEngine, PaceCalculatorElite,  # noqa: E402
                               RunPredictionsEngine, TerrainType)
from engines.strength import (AdaptiveLoadInput, RoadToRaidStrength,  # noqa: E402
                              StrengthEngineService, PREngine, PRRecord)

# Legacy engines (B3-B7)
from build5_road_to_raid.road_to_raid_service import RoadToRaidService  # noqa: E402
from build6_analytics_engine.analytics_service import AnalyticsService  # noqa: E402
from build7_auto_plan_generator.auto_plan_service import AutoPlanGeneratorService  # noqa: E402


class CoachAPI:
    """Single façade over every engine. The FastAPI app calls only this class."""

    def __init__(self) -> None:
        self.daily_engine = DailyDecisionEngine()
        self.budget_engine = FatigueBudgetEngine()
        self.arbitration = GoalArbitrationEngine()
        self.nutrition = NutritionService()
        self.hr_zones = HRZonesEngine()
        self.predictions = RunPredictionsEngine()
        self.paces = PaceCalculatorElite()
        self.strength = StrengthEngineService()
        self.pr_engine = PREngine()
        self.raid_strength = RoadToRaidStrength()
        self.road_to_raid = RoadToRaidService()
        self.analytics = AnalyticsService()
        self.auto_plan_service = AutoPlanGeneratorService()

    # ---- COACH ----
    def daily_decision(self, payload: dict) -> dict:
        ctx = DailyContext(
            day_of_week=payload["day_of_week"],
            is_work_day=payload["is_work_day"],
            week_type=WeekType(payload["week_type"]),
            readiness=payload["readiness"],
            fatigue=payload["fatigue"],
            sleep_quality=payload["sleep_quality"],
            pain_flag=payload.get("pain_flag", False),
            sciatic_flare=payload.get("sciatic_flare", False),
            budget_consumed_pct=payload.get("budget_consumed_pct", 0),
            days_since_rest=payload.get("days_since_rest", 0),
            last_two_disciplines=payload.get("last_two_disciplines", []),
            weeks_to_main_goal=payload.get("weeks_to_main_goal"),
        )
        d = self.daily_engine.decide(ctx)
        return {
            "best_action": d.best_action.value,
            "secondary_action": d.secondary_action.value if d.secondary_action else None,
            "duration_min": d.duration_min,
            "intensity_cap": d.intensity_cap,
            "reason": d.reason,
            "alternatives": d.alternatives,
            "safety_notes": d.safety_notes,
        }

    def weekly_budget(self, payload: dict) -> dict:
        sessions = [SessionLoad(Discipline(s["discipline"]), s["duration_min"],
                                s["intensity"], s.get("terrain_factor", 1.0),
                                s.get("load_carried_kg", 0.0))
                    for s in payload.get("sessions", [])]
        rep = self.budget_engine.report(WeekType(payload["week_type"]), sessions)
        return {
            "status": rep.status.value, "consumed_su": rep.consumed_su,
            "budget_su": rep.budget_su, "remaining_su": rep.remaining_su,
            "consumed_pct": rep.consumed_pct,
            "per_discipline_su": rep.per_discipline_su,
            "hard_sessions_done": rep.hard_sessions_done,
            "warnings": rep.warnings,
        }

    def arbitrate_goals(self, payload: dict) -> dict:
        goals = [TrainingGoal(g["goal_id"], g["name"], Discipline(g["discipline"]),
                              g["target_date_weeks"], g["priority"])
                 for g in payload["goals"]]
        res = self.arbitration.arbitrate(goals)
        return {
            "primary_goal_id": res.primary_goal_id,
            "ranked_goal_ids": res.ranked_goal_ids,
            "allocation_pct": res.allocation_pct,
            "rationale": res.rationale,
        }

    # ---- RUN ----
    def hr_profile(self, payload: dict) -> dict:
        fc_max = payload.get("fc_max") or self.hr_zones.fcmax_tanaka(payload["age"])
        p = self.hr_zones.compute(fc_max, payload.get("fc_rest"))
        return {"fc_max": p.fc_max, "method": p.method,
                "zones": [{"zone": z.zone.value, "min_bpm": z.min_bpm,
                           "max_bpm": z.max_bpm, "description": z.description}
                          for z in p.zones]}

    def run_predictions(self, payload: dict) -> dict:
        r = self.predictions.predict(payload["distance_km"], payload["time_sec"])
        return {"vma_estimate_kmh": r.vma_estimate_kmh,
                "cooper_estimate_m": r.cooper_estimate_m,
                "predictions": [{"label": p.label, "time_sec": p.predicted_time_sec,
                                 "pace_sec_km": p.predicted_pace_sec_km}
                                for p in r.predictions]}

    def pace_table(self, payload: dict) -> dict:
        t = self.paces.table(payload["vma_kmh"],
                             TerrainType(payload.get("terrain", "road")),
                             payload.get("elevation_gain_m_per_km", 0.0),
                             payload.get("load_kg", 0.0))
        return {"vma_kmh": t.vma_kmh, "terrain": t.terrain.value,
                "targets": [{"zone": x.zone.value,
                             "pace_fast": PaceCalculatorElite.fmt(x.pace_min_sec_km),
                             "pace_slow": PaceCalculatorElite.fmt(x.pace_max_sec_km)}
                            for x in t.targets]}

    # ---- STRENGTH ----
    def generate_strength_session(self, payload: dict) -> dict:
        s = self.strength.generate(
            AdaptiveLoadInput(
                payload["recovery_score"], payload["sleep_quality"],
                payload.get("pain_flag", False), payload.get("hrv_trend", "stable"),
                payload.get("run_load_7d", 0), payload.get("crossfit_load_7d", 0),
                payload.get("strength_load_7d", 0),
                payload.get("sessions_since_deload", 0)),
            payload.get("week_in_block", 0), payload.get("weeks_to_goal"),
            payload.get("athlete_level", "intermediate"),
            payload.get("raid_focus", True),
            payload.get("recent_family_ids", []), payload.get("seed", ""))
        return {"session_id": s.session_id, "family_id": s.family_id,
                "level": s.level, "phase": s.phase.value,
                "duration_min": s.duration_min, "expected_load": s.expected_load,
                "load_decision": s.load_decision.value,
                "blocks": [{"movement_id": b.movement_id, "sets": b.sets,
                            "reps": b.reps, "intensity_pct": b.intensity_pct,
                            "rest_sec": b.rest_sec, "method": b.method.value,
                            "notes": b.notes} for b in s.blocks]}

    def pr_estimate(self, payload: dict) -> dict:
        est = self.pr_engine.estimate(PRRecord(payload["movement_id"],
                                               payload["weight_kg"],
                                               payload["reps"],
                                               payload.get("date", "2026-01-01")))
        return {"movement_id": est.movement_id, "e1rm": est.e1rm,
                "rm3": est.rm3, "rm5": est.rm5, "rm8": est.rm8}

    def raid_strength_report(self, payload: dict) -> dict:
        r = self.raid_strength.analyze(payload["current"], payload["bodyweight_kg"],
                                       payload.get("tier", "pass"))
        return {"global_readiness_pct": r.global_readiness_pct,
                "primary_focus": r.primary_focus,
                "estimated_weeks_to_ready": r.estimated_weeks_to_ready,
                "recommendation": r.recommendation,
                "targets": [{"name": t.name, "current": t.current_value,
                             "target": t.target_value, "unit": t.unit,
                             "gap_pct": t.gap_pct, "priority": t.priority}
                            for t in r.targets]}

    # ---- PLANS / RAID (legacy engines B5/B7) ----
    def raid_plan(self, payload: dict) -> dict:
        # Les 5 dimensions du profiler sont obligatoires : valeurs neutres
        # par défaut, surchargées par les inputs fournis
        profile_inputs = {"endurance": 50.0, "mountain": 50.0, "portage": 50.0,
                          "speed": 50.0, "technical": 50.0,
                          **payload.get("profile_inputs", {})}
        plan = self.road_to_raid.build_plan(
            duration_weeks=payload.get("duration_weeks", 16),
            goal=payload.get("goal", "mountain_raid"),
            **profile_inputs)
        return {"duration_weeks": plan.duration_weeks if hasattr(plan, "duration_weeks") else payload.get("duration_weeks", 16),
                "summary": str(plan)[:2000]}

    def auto_plan(self, payload: dict) -> dict:
        p = self.auto_plan_service.generate_plan(
            goal_type=payload["goal_type"],
            target_event=payload["goal_name"],
            duration_weeks=payload["duration_weeks"],
            analytics=payload.get("analytics"))
        weeks = getattr(p, "weeks", [])
        days = getattr(p, "days", [])
        rules = getattr(p, "adaptive_rules", [])
        return {"goal": payload["goal_name"],
                "duration_weeks": payload["duration_weeks"],
                "weeks": len(weeks), "days": len(days),
                "adaptive_rules": len(rules)}

    # ---- NUTRITION ----
    def daily_macros(self, payload: dict) -> dict:
        profile = NutritionProfile(
            payload["weight_kg"], payload["height_cm"], payload["age"],
            payload.get("sex", "m"), payload.get("body_fat_pct"),
            payload.get("target_weight_kg", payload["weight_kg"]),
            NutritionPhase(payload.get("phase", "recomp")))
        t = self.nutrition.daily(profile, ActivityLevel(payload.get("activity", "moderate")))
        return {"day_type": t.day_type.value, "calories": t.calories,
                "protein_g": t.protein_g, "carbs_g": t.carbs_g,
                "fat_g": t.fat_g, "water_l": t.water_l, "notes": t.notes}

    def selection_day_nutrition(self, payload: dict) -> dict:
        plan = self.nutrition.race.selection_day_plan(payload["weight_kg"])
        return {"day_minus_1": plan.day_minus_1, "morning": plan.morning,
                "during": plan.during, "after": plan.after,
                "hydration": plan.hydration}
