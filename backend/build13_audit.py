from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db.database import CACHE_TTL, CacheLayer, Database  # noqa: E402
from db.repositories.repositories import (AthleteRepository,  # noqa: E402
                                          BenchmarkRepository,
                                          DecisionRepository,
                                          MetricsRepository, PlanRepository,
                                          PRRepository, SessionRepository)
from db.schema import TABLES  # noqa: E402
from engines.selection_wods import (EQUIPMENT_STANDARDS,  # noqa: E402
                                    OFFICIAL_BENCHMARKS,
                                    SelectionWODGenerator)


def _db() -> Database:
    return Database(":memory:")


def test_13a_schema_creation():
    db = _db()
    created = db.tables()
    for t in TABLES:
        assert t in created, f"missing table {t}"


def test_13b_athlete_crud():
    db = _db()
    repo = AthleteRepository(db)
    uid = repo.create_user("athlete@raid.fr", "hash")
    aid = repo.create_profile(uid, "Athlète RAID", height_cm=172, weight_kg=75,
                              target_weight_kg=79, fc_max=186,
                              main_goal="RAID selection 2029",
                              injuries=[{"zone": "L5-S1", "type": "sciatique"}])
    p = repo.get_profile(aid)
    assert p["weight_kg"] == 75 and "L5-S1" in p["injuries"]
    repo.update_profile(aid, weight_kg=76.5)
    assert repo.get_profile(aid)["weight_kg"] == 76.5


def test_13c_sessions_and_acwr_data():
    db = _db()
    arepo, srepo = AthleteRepository(db), SessionRepository(db)
    aid = arepo.create_profile(arepo.create_user("a@b.c", "h"), "A")
    for i in range(10):
        sid = srepo.record(aid, "run", f"2026-06-{i+1:02d}", 60, 6.0, 21.6,
                           {"family": "z2"}, family_id=f"fam_{i % 4}")
        srepo.complete(sid, {"rpe_felt": 6})
    assert len(srepo.last_n(aid, 5)) == 5
    su = srepo.stress_units_between(aid, "2026-06-01", "2026-06-07")
    assert su == 21.6 * 7
    fams = srepo.recent_family_ids(aid, 20)
    assert len(fams) == 10 and "fam_0" in fams


def test_13d_pr_and_benchmarks():
    db = _db()
    arepo = AthleteRepository(db)
    aid = arepo.create_profile(arepo.create_user("a@b.c", "h"), "A")
    pr = PRRepository(db)
    pr.record(aid, "bench", 95, 1, 95.0, "2026-06-11", 75)
    pr.record(aid, "bench", 100, 1, 100.0, "2026-09-01", 76)
    assert pr.best_e1rm(aid, "bench") == 100.0
    assert len(pr.history(aid, "bench")) == 2
    bench = BenchmarkRepository(db)
    bench.record(aid, "wod_selection_pdc_2026", 7.0, "minutes_completed",
                 "2026-06-15", {"fail_minute_reps": 23})
    bench.record(aid, "wod_selection_pdc_2026", 9.0, "minutes_completed", "2026-09-15")
    prog = bench.progression(aid, "wod_selection_pdc_2026")
    assert len(prog) == 2 and prog[1]["result_value"] > prog[0]["result_value"]


def test_13e_metrics_upsert():
    db = _db()
    arepo = AthleteRepository(db)
    aid = arepo.create_profile(arepo.create_user("a@b.c", "h"), "A")
    m = MetricsRepository(db)
    m.upsert(aid, "2026-06-11", readiness=75, fatigue=40, sciatic_flare=0)
    m.upsert(aid, "2026-06-11", readiness=70, sciatic_flare=1)  # same day update
    latest = m.latest(aid)
    assert latest["readiness"] == 70 and latest["sciatic_flare"] == 1


def test_13f_plans_single_active():
    db = _db()
    arepo = AthleteRepository(db)
    aid = arepo.create_profile(arepo.create_user("a@b.c", "h"), "A")
    plans = PlanRepository(db)
    plans.save(aid, "raid", "Plan 1", 16, "2026-06-15", {"weeks": []})
    plans.save(aid, "raid", "Plan 2", 12, "2026-07-01", {"weeks": []})
    active = plans.active(aid)
    assert active["goal_name"] == "Plan 2"  # plan 1 auto-abandoned


def test_13g_decisions_and_cache():
    db = _db()
    arepo = AthleteRepository(db)
    aid = arepo.create_profile(arepo.create_user("a@b.c", "h"), "A")
    dec = DecisionRepository(db)
    dec.log(aid, "2026-06-11", "daily", {"readiness": 75}, {"best_action": "run"})
    assert len(dec.for_date(aid, "2026-06-11")) == 1
    cache = CacheLayer()
    cache.set("coach_decision:1:2026-06-11", {"best_action": "run"},
              CACHE_TTL["coach_decision"])
    assert cache.get("coach_decision:1:2026-06-11")["best_action"] == "run"
    cache.invalidate("coach_decision:1:2026-06-11")
    assert cache.get("coach_decision:1:2026-06-11") is None


def test_13h_selection_wods_official():
    assert len(OFFICIAL_BENCHMARKS) == 2
    pdc = OFFICIAL_BENCHMARKS[0]
    assert pdc.wod_format == "death_by_emom" and pdc.is_official_benchmark
    assert any("11 tractions" in d for d in pdc.description)
    force = OFFICIAL_BENCHMARKS[1]
    assert any("115 kg" in d for d in force.description)
    assert any("mannequin" in d.lower() for d in force.description)
    assert EQUIPMENT_STANDARDS["dummy_kg"] == 75.0
    assert EQUIPMENT_STANDARDS["ram_kg"] == 16.0


def test_13i_selection_wod_variants():
    gen = SelectionWODGenerator()
    ids = set()
    for i in range(30):
        v1 = gen.death_by_variant(f"seed{i}")
        v2 = gen.time_cap_variant(f"seed{i}")
        ids.add(v1.wod_id); ids.add(v2.wod_id)
        assert v1.wod_format == "death_by_emom" and len(v1.description) >= 5
        assert v2.wod_format == "time_cap_loaded"
        assert any("Max distance" in d for d in v2.description)
    assert len(ids) == 60  # all unique
    # Anti-repetition: same seed avoids recent ids
    recent = [gen.death_by_variant("dup").wod_id]
    alt = gen.death_by_variant("dup", recent)
    assert alt.wod_id not in recent
    # Progression block: benchmarks at start and end
    block = gen.progression_block(8, "block1")
    assert block[0].is_official_benchmark and block[-1].is_official_benchmark
    assert len(block) == 2 + 6 + 2


TESTS = [test_13a_schema_creation, test_13b_athlete_crud,
         test_13c_sessions_and_acwr_data, test_13d_pr_and_benchmarks,
         test_13e_metrics_upsert, test_13f_plans_single_active,
         test_13g_decisions_and_cache, test_13h_selection_wods_official,
         test_13i_selection_wod_variants]


def run_audit() -> dict:
    exceptions = 0
    checks = {}
    for t in TESTS:
        try:
            t(); checks[t.__name__] = True
        except Exception:
            exceptions += 1; checks[t.__name__] = False

    # 100-sample fuzz: full persistence round-trips + WOD generation
    fuzz_errors = 0
    db = _db()
    arepo, srepo = AthleteRepository(db), SessionRepository(db)
    mrepo, gen = MetricsRepository(db), SelectionWODGenerator()
    aid = arepo.create_profile(arepo.create_user("fuzz@x.y", "h"), "Fuzz")
    for i in range(100):
        try:
            sid = srepo.record(aid, ["run", "crossfit", "strength", "swim"][i % 4],
                               f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                               30 + i % 90, 1 + (i % 9), 10.0 + i,
                               {"i": i}, family_id=f"fam_{i % 15}")
            if i % 2:
                srepo.complete(sid, {"rpe": i % 10})
            mrepo.upsert(aid, f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                         readiness=i % 100, fatigue=(i * 3) % 100)
            (gen.death_by_variant if i % 2 else gen.time_cap_variant)(f"fz{i}")
        except Exception:
            fuzz_errors += 1
    checks["fuzz_100_samples"] = fuzz_errors == 0
    exceptions += fuzz_errors

    status = "PASS" if exceptions == 0 and all(checks.values()) else "FAIL"
    return {
        "build": "13",
        "module": "Persistance (schéma 10 tables, 7 repositories, cache) + WODs Sélection officiels",
        "status": status, "samples": 100, "exceptions": exceptions, "checks": checks,
        "tables": TABLES,
        "official_benchmarks": [w.wod_id for w in OFFICIAL_BENCHMARKS],
        "note": "Schéma canonique PostgreSQL, exécuté ici sur SQLite (même DDL). Redis: interface compatible, fallback mémoire en sandbox.",
        "decision": "BUILD 13 VALIDATED" if status == "PASS" else "BUILD 13 FAILED",
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
    with open("build13-report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ("status", "exceptions", "decision")}, indent=2))
