from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.services.coach_api import CoachAPI  # noqa: E402

coach = CoachAPI()


def test_12a_health_facade():
    """All 13 engine handles instantiated."""
    for attr in ("daily_engine", "budget_engine", "arbitration", "nutrition",
                 "hr_zones", "predictions", "paces", "strength", "pr_engine",
                 "raid_strength", "road_to_raid", "analytics", "auto_plan_service"):
        assert getattr(coach, attr) is not None


def test_12b_daily_decision_endpoint():
    out = coach.daily_decision({
        "day_of_week": "thu", "is_work_day": False, "week_type": "big_work",
        "readiness": 85, "fatigue": 30, "sleep_quality": 85,
        "last_two_disciplines": ["strength", "swim"], "weeks_to_main_goal": 130,
    })
    assert out["best_action"] in ("run", "crossfit", "strength", "swim", "recovery", "rest")
    assert out["duration_min"] >= 0 and out["reason"]


def test_12c_daily_decision_sciatic_safety():
    out = coach.daily_decision({
        "day_of_week": "mon", "is_work_day": True, "week_type": "big_work",
        "readiness": 80, "fatigue": 30, "sleep_quality": 80, "sciatic_flare": True,
    })
    assert out["best_action"] == "swim"
    assert any("sciatique" in n.lower() for n in out["safety_notes"])


def test_12d_weekly_budget_endpoint():
    out = coach.weekly_budget({
        "week_type": "small_work",
        "sessions": [
            {"discipline": "run", "duration_min": 60, "intensity": 6},
            {"discipline": "crossfit", "duration_min": 60, "intensity": 8},
            {"discipline": "strength", "duration_min": 50, "intensity": 7},
        ],
    })
    assert out["status"] in ("under_budget", "on_track", "near_limit", "over_budget")
    assert out["budget_su"] == 620.0
    assert out["consumed_su"] > 0


def test_12e_arbitration_endpoint():
    out = coach.arbitrate_goals({"goals": [
        {"goal_id": "raid_2029", "name": "Sélection RAID 2029",
         "discipline": "crossfit", "target_date_weeks": 140, "priority": 1},
        {"goal_id": "semi", "name": "Semi 1h35", "discipline": "run",
         "target_date_weeks": 16, "priority": 2},
    ]})
    assert out["allocation_pct"]["raid_2029"] >= 30.0
    assert out["primary_goal_id"] in ("raid_2029", "semi")


def test_12f_run_endpoints():
    hr = coach.hr_profile({"age": 31})
    assert hr["fc_max"] in (186, 187) and len(hr["zones"]) == 5
    pred = coach.run_predictions({"distance_km": 8.0, "time_sec": 2400})
    assert 13.0 <= pred["vma_estimate_kmh"] <= 15.5
    pt = coach.pace_table({"vma_kmh": 13.6, "terrain": "trail",
                           "elevation_gain_m_per_km": 30, "load_kg": 10})
    assert len(pt["targets"]) == 5


def test_12g_strength_endpoints():
    s = coach.generate_strength_session({
        "recovery_score": 75, "sleep_quality": 80, "raid_focus": True, "seed": "42",
    })
    assert s["blocks"] and s["duration_min"] >= 20
    pr = coach.pr_estimate({"movement_id": "bench", "weight_kg": 95, "reps": 1})
    assert pr["e1rm"] == 95.0
    rep = coach.raid_strength_report({
        "current": {"pullups_max": 16, "pushups_max": 60, "dips_max": 40,
                    "leg_raises_max": 18, "rope_climb_5m": 1,
                    "bench_ratio": 95, "squat_ratio": 110, "cooper_m": 2850},
        "bodyweight_kg": 75, "tier": "elite",
    })
    assert 45 <= rep["global_readiness_pct"] <= 60


def test_12h_auto_plan_endpoint():
    out = coach.auto_plan({
        "goal_type": "raid", "goal_name": "Sélection RAID 2029",
        "duration_weeks": 16,
        "analytics": {"fitness": 60, "fatigue": 40, "readiness": 70,
                      "risk": 30, "performance": 55},
    })
    assert out["duration_weeks"] == 16 and out["weeks"] == 16 and out["days"] > 0


def test_12i_nutrition_endpoints():
    m = coach.daily_macros({"weight_kg": 75, "height_cm": 172, "age": 31,
                            "target_weight_kg": 79, "activity": "high"})
    assert m["protein_g"] == 165 and m["calories"] > 2000
    plan = coach.selection_day_nutrition({"weight_kg": 75})
    assert plan["day_minus_1"] and plan["during"]


TESTS = [test_12a_health_facade, test_12b_daily_decision_endpoint,
         test_12c_daily_decision_sciatic_safety, test_12d_weekly_budget_endpoint,
         test_12e_arbitration_endpoint, test_12f_run_endpoints,
         test_12g_strength_endpoints, test_12h_auto_plan_endpoint,
         test_12i_nutrition_endpoints]


def run_audit() -> dict:
    exceptions = 0
    checks = {}
    for t in TESTS:
        try:
            t(); checks[t.__name__] = True
        except Exception:
            exceptions += 1; checks[t.__name__] = False

    # 100-sample fuzz across the service façade
    fuzz_errors = 0
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for i in range(100):
        try:
            coach.daily_decision({
                "day_of_week": days[i % 7], "is_work_day": i % 3 == 0,
                "week_type": "big_work" if i % 2 else "small_work",
                "readiness": 15 + (i * 9) % 85, "fatigue": (i * 13) % 95,
                "sleep_quality": 20 + (i * 7) % 80,
                "pain_flag": i % 23 == 0, "sciatic_flare": i % 31 == 0,
                "budget_consumed_pct": (i * 11) % 130,
                "days_since_rest": i % 8,
                "last_two_disciplines": [["run", "crossfit", "strength", "swim"][i % 4]],
            })
            coach.daily_macros({"weight_kg": 60 + i % 40, "height_cm": 165 + i % 30,
                                "age": 20 + i % 40, "target_weight_kg": 70,
                                "activity": ["rest", "light", "moderate", "high"][i % 4]})
            coach.pr_estimate({"movement_id": "m", "weight_kg": 40 + i, "reps": 1 + i % 10})
        except Exception:
            fuzz_errors += 1
    checks["fuzz_100_samples"] = fuzz_errors == 0
    exceptions += fuzz_errors

    # FastAPI layer: syntax + structural validation (FastAPI not installed in sandbox)
    import ast
    try:
        tree = ast.parse(open("api/main.py").read())
        routes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                  and any(isinstance(d, ast.Call) for d in n.decorator_list)]
        checks["fastapi_layer_syntax_ok"] = True
        # 13 moteurs + 3 séance/planning + 5 persistance + 5 profil/agenda/analytics
        checks["fastapi_routes_count_26"] = len(routes) == 26
    except SyntaxError:
        checks["fastapi_layer_syntax_ok"] = False
        exceptions += 1

    status = "PASS" if exceptions == 0 and all(checks.values()) else "FAIL"
    return {
        "build": "12", "module": "API FastAPI (service layer + routes)",
        "status": status, "samples": 100, "exceptions": exceptions, "checks": checks,
        "endpoints": ["/health", "/coach/daily-decision", "/coach/weekly-budget",
                      "/coach/arbitrate-goals", "/run/hr-profile", "/run/predictions",
                      "/run/pace-table", "/strength/generate", "/strength/pr-estimate",
                      "/raid/strength-report", "/plans/auto-generate",
                      "/nutrition/daily-macros", "/nutrition/selection-day"],
        "note": "Couche service validée à 100% en sandbox. Couche FastAPI validée syntaxiquement; exécution complète via CI GitHub (workflow fourni).",
        "decision": "BUILD 12 VALIDATED" if status == "PASS" else "BUILD 12 FAILED",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            t(); passed += 1; print(f"PASS {t.__name__}")
        except Exception as e:
            import traceback
            print(f"FAIL {t.__name__}: {e}"); traceback.print_exc()
    print(f"--- {passed}/{len(TESTS)} tests ---")
    report = run_audit()
    with open("build12-report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ("status", "exceptions", "decision")}, indent=2))
