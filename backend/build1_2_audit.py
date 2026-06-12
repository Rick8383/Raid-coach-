"""BUILD 1 & 2 — Audit complet.
Build 1 : Core Domain (Athlete, Goal, Session, Metrics, RaidProfile, Memory)
Build 2 : Run Engine Runtime (110 familles, 660 templates, pipeline complet)
"""
from __future__ import annotations
import json
import sys
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

# BUILD 1
from engines.core.models import (  # noqa: E402
    Athlete, AthleteMemory, DailyMetrics, FatigueZone, Goal, GoalStatus,
    GoalType, PerformanceSnapshot, RaidProfile, ReadinessZone, Session,
    SessionResult, SessionType)
from engines.core.services import FatigueEngine, RaidProfileEngine, ReadinessEngine  # noqa: E402

# BUILD 2
from engines.run_engine.family_registry import RUN_FAMILIES  # noqa: E402
from engines.run_engine.template_factory import ALL_TEMPLATES  # noqa: E402
from engines.run_engine.run_engine_service import generate_session  # noqa: E402
from engines.run_engine.anti_repetition import anti_repetition_score  # noqa: E402
from engines.run_engine.readiness_engine import readiness_score, readiness_zone  # noqa: E402
from engines.run_engine.fatigue_engine import fatigue_ratio, fatigue_zone  # noqa: E402


# ===== BUILD 1 TESTS =====

def test_b1a_athlete_entity():
    a = Athlete(firstname="Test", lastname="RAID", weight_kg=75,
                height_cm=172, birth_date=date(1995, 7, 30))
    a.validate()
    assert a.age == 30 or a.age == 31  # depending on today
    assert 1 <= a.bmi <= 60
    assert a.id is not None


def test_b1b_goal_entity():
    g = Goal(goal_type=GoalType.RAID, priority=1,
             target_date=date(2029, 3, 1), status=GoalStatus.ACTIVE)
    g.validate()
    assert g.weeks_to_target is not None and g.weeks_to_target > 0


def test_b1c_session_entity():
    s = Session(session_type=SessionType.RUN, family="raid_tempo_hybrid",
                planned_duration_min=90, planned_load=55.0)
    s.validate()
    result = SessionResult(session_id=s.id, duration_min=88, rpe=7, completed=True)
    result.validate()


def test_b1d_daily_metrics_and_readiness():
    m = DailyMetrics(sleep_quality=80, fatigue=35, stress=30,
                     motivation=75, recovery=75)
    m.validate()
    eng = ReadinessEngine()
    score, zone = eng.evaluate(m)
    assert 0 <= score <= 100
    assert zone in ReadinessZone
    assert m.readiness_score == score
    # RED zone: high fatigue + low motivation
    low = DailyMetrics(sleep_quality=30, fatigue=85, stress=80,
                       motivation=20, recovery=25)
    _, z = eng.evaluate(low)
    assert z == ReadinessZone.RED


def test_b1e_fatigue_engine():
    eng = FatigueEngine()
    r, z = eng.evaluate(400, 400)
    assert r == 1.0 and z == FatigueZone.OPTIMAL
    _, z2 = eng.evaluate(620, 400)
    assert z2 == FatigueZone.DANGER
    _, z3 = eng.evaluate(0, 0)
    assert z3 == FatigueZone.OPTIMAL


def test_b1f_raid_profile():
    snap = PerformanceSnapshot(athlete_id=uuid4(), cooper_m=3100,
                               raid_score=65, fitness_score=60,
                               fatigue_score=40, readiness_score=75,
                               vma_kmh=14.0)
    snap.validate()
    profile = RaidProfileEngine().build_from_snapshot(snap, carry_result=55, mountain_result=60)
    profile.validate()
    assert 0 <= profile.raid_score <= 100
    assert profile.weakest_axis in ("endurance", "mountain", "carry", "strength", "resilience")


def test_b1g_athlete_memory():
    mem = AthleteMemory(athlete_id=uuid4())
    mem.record_response("raid_tempo_hybrid", rpe_felt=9.0, rpe_planned=7.0)
    assert "raid_tempo_hybrid" in mem.avoided_families
    mem.record_response("easy_long_run", rpe_felt=5.0, rpe_planned=7.0)
    assert "easy_long_run" in mem.preferred_families
    assert "raid_tempo_hybrid" in mem.response_profile


# ===== BUILD 2 TESTS =====

def test_b2a_registry_count():
    assert len(RUN_FAMILIES) == 110
    ids = {f.id for f in RUN_FAMILIES}
    assert len(ids) == 110, "duplicate family ids"
    categories = {f.category for f in RUN_FAMILIES}
    assert len(categories) == 11, "expected 11 categories"


def test_b2b_template_count():
    assert len(ALL_TEMPLATES) == 660
    ids = {t.id for t in ALL_TEMPLATES}
    assert len(ids) == 660, "duplicate template ids"
    levels = {t.level for t in ALL_TEMPLATES}
    assert levels == {"beginner", "intermediate", "advanced", "deload", "peak", "elite"}


def test_b2c_readiness_engine():
    # fatigue et stress sont des scores inversés : bas = bon
    score = readiness_score(80, 20, 20, 80, 80)
    assert 0 <= score <= 100
    zone = readiness_zone(score)
    assert zone.value == "green"
    assert readiness_zone(readiness_score(10, 90, 90, 10, 10)).value == "red"
    assert readiness_zone(readiness_score(95, 5, 5, 95, 95)).value == "peak"
    # un athlète épuisé ne doit jamais remonter en zone verte
    assert readiness_zone(readiness_score(30, 95, 90, 40, 20)).value == "red"


def test_b2d_fatigue_engine():
    assert fatigue_zone(fatigue_ratio(100, 100)).value == "optimal"
    assert fatigue_zone(fatigue_ratio(150, 100)).value == "danger"
    assert fatigue_zone(fatigue_ratio(0, 0)).value == "optimal"


def test_b2e_session_generation():
    s = generate_session(goal="raid", phase="build",
                         availability_min=90, terrain="trail")
    assert s.family_id and s.template_id
    assert s.duration_min == 90
    assert s.expected_load > 0
    assert s.terrain_type == "trail"
    # Recovery generation
    s2 = generate_session(goal="raid", phase="build",
                          availability_min=60, terrain="road",
                          sleep=20, fatigue=20, stress=20, motivation=20, recovery=20)
    assert s2.family_id  # always returns something


def test_b2f_anti_repetition():
    s = generate_session(goal="raid", phase="build", availability_min=90)
    history = [{"family_id": s.family_id, "variant": s.variant,
                "structure_hash": "x"}]
    # Same family/variant → score = 0
    score = anti_repetition_score(s, history)
    assert score == 0.0
    # Different family → score = 1.0
    s2 = generate_session(goal="10k", phase="build", availability_min=60)
    score2 = anti_repetition_score(s2, [])
    assert score2 == 1.0


def test_b2g_pipeline_variety():
    """50 sessions générées → au moins 10 familles distinctes (variété)."""
    families: set[str] = set()
    for i in range(50):
        s = generate_session(
            goal=["raid", "10k", "trail"][i % 3],
            phase=["base", "build", "peak"][i % 3],
            availability_min=45 + (i % 4) * 15,
            terrain=["road", "trail", "hilly", "mountain"][i % 4])
        families.add(s.family_id)
    assert len(families) >= 10


TESTS_B1 = [test_b1a_athlete_entity, test_b1b_goal_entity, test_b1c_session_entity,
            test_b1d_daily_metrics_and_readiness, test_b1e_fatigue_engine,
            test_b1f_raid_profile, test_b1g_athlete_memory]
TESTS_B2 = [test_b2a_registry_count, test_b2b_template_count, test_b2c_readiness_engine,
            test_b2d_fatigue_engine, test_b2e_session_generation,
            test_b2f_anti_repetition, test_b2g_pipeline_variety]
ALL_TESTS = TESTS_B1 + TESTS_B2


def run_audit() -> dict:
    exceptions = 0
    checks: dict[str, bool] = {}
    for t in ALL_TESTS:
        try:
            t(); checks[t.__name__] = True
        except Exception:
            exceptions += 1; checks[t.__name__] = False

    # 100-sample fuzz
    re_eng = ReadinessEngine()
    fa_eng = FatigueEngine()
    fuzz_errors = 0
    for i in range(100):
        try:
            m = DailyMetrics(sleep_quality=10 + (i * 9) % 90,
                             fatigue=(i * 13) % 100,
                             stress=(i * 7) % 100,
                             motivation=10 + (i * 11) % 90,
                             recovery=10 + (i * 17) % 90)
            re_eng.evaluate(m)
            fa_eng.evaluate(100 + i * 5, max(1, 150 + i * 3 - 100))
            generate_session(
                goal=["raid", "10k", "trail"][i % 3],
                phase=["base", "build", "peak"][i % 3],
                availability_min=30 + (i * 11) % 100,
                terrain=["road", "trail", "mountain", "hilly"][i % 4],
                sleep=10 + (i * 9) % 90, fatigue=(i * 13) % 100,
                stress=(i * 7) % 100, motivation=10 + (i * 11) % 90,
                recovery=10 + (i * 17) % 90)
        except Exception:
            fuzz_errors += 1
    checks["fuzz_100_samples"] = fuzz_errors == 0
    exceptions += fuzz_errors

    status = "PASS" if exceptions == 0 and all(checks.values()) else "FAIL"
    return {
        "builds": "1 + 2", "module": "Core Domain + Run Engine Runtime",
        "status": status, "samples": 100, "exceptions": exceptions,
        "checks": checks,
        "stats": {"families": len(RUN_FAMILIES), "templates": len(ALL_TEMPLATES)},
        "decision": "BUILD 1+2 VALIDATED" if status == "PASS" else "BUILD 1+2 FAILED",
    }


if __name__ == "__main__":
    passed = 0
    print("=== BUILD 1 — Core Domain ===")
    for t in TESTS_B1:
        try:
            t(); passed += 1; print(f"  PASS {t.__name__}")
        except Exception as e:
            import traceback
            print(f"  FAIL {t.__name__}: {e}"); traceback.print_exc()
    print(f"\n=== BUILD 2 — Run Engine Runtime ===")
    for t in TESTS_B2:
        try:
            t(); passed += 1; print(f"  PASS {t.__name__}")
        except Exception as e:
            import traceback
            print(f"  FAIL {t.__name__}: {e}"); traceback.print_exc()
    print(f"\n--- {passed}/{len(ALL_TESTS)} tests ---")
    report = run_audit()
    with open("build1_2_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ("status", "exceptions", "stats", "decision")}, indent=2))
