from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engines.rcos import (AnnualPlanner, AthleteMemory, BestActionToday,  # noqa
                          DigitalTwin, LifeConstraint, LifeConstraintKind,
                          LifeEngine, MemoryEntry, MemoryKind, PriorityEngine,
                          RCOSService, SeasonPhase, TwinState)


def test_14a_memory_learn_and_decay():
    mem = AthleteMemory()
    mem.remember(MemoryEntry(MemoryKind.SESSION_RESPONSE, "2026-06-01",
                             "Répond très bien aux EMOM tractions", 2.0, ["+"]))
    mem.remember(MemoryEntry(MemoryKind.SESSION_RESPONSE, "2026-06-02",
                             "Mauvaise récup après 2 jours VMA consécutifs", 2.0, ["-"]))
    mem.remember(MemoryEntry(MemoryKind.INJURY_SIGNAL, "2026-06-03",
                             "Gêne sciatique après deadlift lourd en fatigue", 3.0))
    d = mem.digest()
    assert d.works_well and d.works_poorly and d.risk_signals
    # Decay: injury signals persist far longer than session responses
    mem.apply_decay(periods_30d=12)
    d2 = mem.digest()
    assert d2.risk_signals  # still remembered after a year
    sciatic = [e for e in mem.entries if e.kind == MemoryKind.INJURY_SIGNAL][0]
    session = [e for e in mem.entries if e.kind == MemoryKind.SESSION_RESPONSE]
    assert all(sciatic.weight > e.weight for e in session) if session else True


def test_14b_memory_capacity():
    mem = AthleteMemory()
    for i in range(600):
        mem.remember(MemoryEntry(MemoryKind.SESSION_RESPONSE, f"2026-01-{(i % 28) + 1:02d}",
                                 f"note {i}", 0.5 + (i % 10) / 10))
    assert len(mem.entries) <= AthleteMemory.MAX_ENTRIES


def test_14c_digital_twin_banister():
    twin = DigitalTwin()
    # 6 weeks of consistent training: fitness builds, form goes negative then stabilizes
    for _ in range(42):
        twin.ingest_day(60.0)
    assert twin.state.fitness > 35  # converging toward 60
    assert twin.state.fatigue > twin.state.fitness  # ATL converges faster
    assert twin.form_label() in ("neutral", "fatigued")
    # Taper restores form
    projected = twin.taper_projection(days=14, taper_load=12.0)
    assert projected > twin.state.form


def test_14d_twin_overreach_detection():
    twin = DigitalTwin()
    for _ in range(14):
        twin.ingest_day(120.0)  # brutal block
    assert twin.form_label() in ("fatigued", "overreached")


def test_14e_life_engine():
    life = LifeEngine()
    life.add(LifeConstraint(LifeConstraintKind.WORK_SHIFT, "2026-06-10",
                            "2026-06-14", 0.3, "grande semaine police"))
    life.add(LifeConstraint(LifeConstraintKind.FAMILY, "2026-06-12",
                            "2026-06-12", 0.5, "événement famille"))
    assert life.capacity_for("2026-06-11") == 0.7
    assert life.capacity_for("2026-06-12") == 0.35  # cumulative
    assert life.capacity_for("2026-06-20") == 1.0
    assert len(life.active_notes("2026-06-12")) == 2


def test_14f_annual_planner_retro():
    plan = AnnualPlanner().build(weeks_to_selection=140)  # ~sélection 2029
    assert plan.selection_week == 140
    assert plan.blocks[-1].phase == SeasonPhase.SELECTION
    assert plan.blocks[-2].phase == SeasonPhase.TAPER
    phases = {b.phase for b in plan.blocks}
    assert {SeasonPhase.BASE, SeasonPhase.BUILD, SeasonPhase.PEAK} <= phases
    assert any("benchmarks officiels" in m for m in plan.key_milestones)
    # SU targets respect police rhythm (small week > big week)
    for b in plan.blocks:
        assert b.target_weekly_su[1] >= b.target_weekly_su[0]


def test_14g_planner_short_horizon():
    plan = AnnualPlanner().build(weeks_to_selection=10)
    assert plan.selection_week == 10
    plan.validate()


def test_14h_priority_engine():
    assert PriorityEngine.rank("neutral", ["gêne sciatique récente"], 100, 1.0)[0] == "protéger_le_dos"
    assert PriorityEngine.rank("overreached", [], 100, 1.0)[0] == "récupération"
    assert PriorityEngine.rank("fresh", [], 100, 1.0)[0] == "développement_prioritaire"
    assert PriorityEngine.rank("neutral", [], 3, 1.0)[0] == "fraîcheur"
    assert PriorityEngine.rank("neutral", [], 100, 0.3)[0] == "maintien_minimal"


def test_14i_best_action_today_integration():
    svc = RCOSService()
    svc.memory.remember(MemoryEntry(MemoryKind.INJURY_SIGNAL, "2026-06-01",
                                    "Sciatique L5-S1 sensible après DL lourd", 3.0))
    svc.memory.remember(MemoryEntry(MemoryKind.SESSION_RESPONSE, "2026-06-05",
                                    "Excellent sur les blocs gym denses", 2.0, ["+"]))
    for _ in range(28):
        svc.twin.ingest_day(55.0)
    svc.life.add(LifeConstraint(LifeConstraintKind.WORK_SHIFT, "2026-06-11",
                                "2026-06-15", 0.25, "grande semaine"))
    plan = svc.planner.build(140)
    bat = svc.best_action_today(plan, current_week=2, date="2026-06-12",
                                daily_action_hint="Run Z2 60' + gym skills 25'")
    assert isinstance(bat, BestActionToday)
    assert bat.season_context == "Sélection dans 138 semaines"
    assert bat.memory_notes and bat.if_only_one_thing
    assert "75%" in bat.action or "Récupération" in bat.action


TESTS = [test_14a_memory_learn_and_decay, test_14b_memory_capacity,
         test_14c_digital_twin_banister, test_14d_twin_overreach_detection,
         test_14e_life_engine, test_14f_annual_planner_retro,
         test_14g_planner_short_horizon, test_14h_priority_engine,
         test_14i_best_action_today_integration]


def run_audit() -> dict:
    exceptions = 0
    checks = {}
    for t in TESTS:
        try:
            t(); checks[t.__name__] = True
        except Exception:
            exceptions += 1; checks[t.__name__] = False

    # 100-sample fuzz across RCOS
    fuzz_errors = 0
    form_labels: set[str] = set()
    for i in range(100):
        try:
            svc = RCOSService()
            for d in range(i % 50 + 5):
                svc.twin.ingest_day((d * 17 + i * 7) % 140)
            form_labels.add(svc.twin.form_label())
            if i % 3 == 0:
                svc.memory.remember(MemoryEntry(
                    list(MemoryKind)[i % 5], "2026-06-01", f"obs {i}",
                    0.5 + (i % 25) / 10))
                svc.memory.apply_decay(i % 6)
            plan = svc.planner.build(10 + (i * 13) % 200)
            week = i % plan.weeks_total
            svc.best_action_today(plan, week, "2026-06-12", "séance test")
        except Exception:
            fuzz_errors += 1
    checks["fuzz_100_samples"] = fuzz_errors == 0
    checks["multiple_form_states_seen"] = len(form_labels) >= 2
    exceptions += fuzz_errors

    status = "PASS" if exceptions == 0 and all(checks.values()) else "FAIL"
    return {
        "build": "14",
        "module": "RCOS (Athlete Memory + Digital Twin + Life Engine + Annual Planner + Best Action Today)",
        "status": status, "samples": 100, "exceptions": exceptions, "checks": checks,
        "form_states_detected": sorted(form_labels),
        "decision": "BUILD 14 VALIDATED" if status == "PASS" else "BUILD 14 FAILED",
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
    with open("build14-report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ("status", "exceptions", "decision")}, indent=2))
