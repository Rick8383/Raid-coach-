"""Tests unitaires API — couvre les 13 endpoints moteurs + 5 endpoints persistance.

Complète les audits build*_audit.py (qui valident les moteurs en profondeur) :
ici on valide le contrat HTTP réel (statuts, validation Pydantic, formes de réponse).
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["RAID_COACH_DB"] = ":memory:"

import api.persistence
import api.main

importlib.reload(api.persistence)
importlib.reload(api.main)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(api.main.app)


# ---------- Santé ----------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- Planning 3/2/2/3 ----------
def test_schedule_day_anchor(client):
    r = client.post("/schedule/day", json={"date": "2026-06-15"})
    assert r.status_code == 200
    body = r.json()
    assert body["week_type"] == "big_work"
    assert body["is_work_day"] is True


def test_schedule_week(client):
    r = client.post("/schedule/week", json={"date": "2026-06-13"})
    assert r.status_code == 200
    body = r.json()
    assert body["week_type"] == "small_work"
    assert len(body["days"]) == 7


# ---------- Séance détaillée ----------
def test_session_off_day_is_double(client):
    # 13/06 = samedi petite semaine → jour OFF, double séance
    r = client.post("/coach/session", json={
        "date": "2026-06-13", "readiness": 75, "fatigue": 35, "sleep_quality": 80})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"]["secondary_action"] is not None
    session = body["session"]
    kinds = {ph["kind"] for ph in session["phases"]}
    assert {"warmup", "main", "cooldown"} <= kinds
    assert any(ph["items"] for ph in session["phases"] if ph["kind"] == "main")


def test_session_work_day_is_single_short(client):
    # 15/06 = lundi grande semaine → service, séance unique courte
    r = client.post("/coach/session", json={
        "date": "2026-06-15", "readiness": 70, "fatigue": 40, "sleep_quality": 70})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"]["secondary_action"] is None
    assert body["session"]["duration_min"] <= 55


def test_session_sciatic_flare_is_safe(client):
    r = client.post("/coach/session", json={
        "date": "2026-06-13", "readiness": 80, "fatigue": 20,
        "sleep_quality": 85, "sciatic_flare": True})
    assert r.status_code == 200
    body = r.json()
    assert body["session"]["discipline"] == "swim"
    assert body["session"]["safety_notes"]


def test_session_explicit_context_overrides_schedule(client):
    # sans date : on fournit le contexte à la main
    r = client.post("/coach/session", json={
        "day_of_week": "wed", "is_work_day": False, "week_type": "big_work",
        "readiness": 75, "fatigue": 35, "sleep_quality": 80})
    assert r.status_code == 200
    assert r.json()["session"]["phases"]


# ---------- Profil athlète ----------
def test_profile_seeded_with_real_data(client):
    body = client.get("/profile").json()
    assert body["height_cm"] == 172.0
    assert body["main_goal"] == "Sélection RAID 2029"
    # maxes actuels assemblés depuis les benchmarks
    assert body["current"]["pullups_max"] == 16.0
    assert body["current"]["cooper_m"] == 2850.0


def test_profile_update_and_reflect(client):
    r = client.patch("/profile", json={"weight_kg": 74.0, "fc_max": 188})
    assert r.status_code == 200
    body = r.json()
    assert body["weight_kg"] == 74.0
    assert body["fc_max"] == 188


def test_profile_update_rejects_out_of_range(client):
    r = client.patch("/profile", json={"weight_kg": 999})
    assert r.status_code == 422


def test_profile_current_reflects_new_benchmark(client):
    client.post("/benchmarks/record", json={
        "benchmark_id": "pullups_max", "result_value": 18,
        "result_unit": "reps", "test_date": "2026-07-01"})
    body = client.get("/profile").json()
    assert body["current"]["pullups_max"] == 18.0


# ---------- Agenda ----------
def test_agenda_week_has_intent_and_done(client):
    client.post("/sessions/complete", json={
        "discipline": "strength", "session_date": "2026-06-17",
        "duration_min": 60, "intensity_rpe": 7})
    w = client.post("/agenda/week", json={"date": "2026-06-15"}).json()
    assert w["week_type"] == "big_work"
    wed = next(d for d in w["days"] if d["day_of_week"] == "wed")
    assert wed["intent"]["focus"] == "double"   # mercredi grande semaine = OFF
    assert wed["done"]["discipline"] == "strength"
    mon = next(d for d in w["days"] if d["day_of_week"] == "mon")
    assert mon["intent"]["focus"] == "single"   # lundi grande semaine = service


# ---------- Générateur par discipline ----------
def test_generate_run(client):
    r = client.post("/generate", json={"discipline": "run", "seed": "t1"})
    assert r.status_code == 200
    body = r.json()
    assert body["discipline"] == "run"
    assert any(ph["kind"] == "main" and ph["items"] for ph in body["phases"])


def test_generate_strength(client):
    r = client.post("/generate", json={"discipline": "strength", "seed": "t2"})
    assert r.status_code == 200
    assert r.json()["discipline"] == "strength"


def test_generate_wod(client):
    r = client.post("/generate", json={"discipline": "crossfit", "seed": "t3", "wod_kind": "time_cap"})
    assert r.status_code == 200
    assert r.json()["phases"]


def test_generate_rejects_unknown_discipline(client):
    assert client.post("/generate", json={"discipline": "yoga"}).status_code == 422


def test_generate_varies_with_seed(client):
    titles = set()
    for i in range(6):
        r = client.post("/generate", json={"discipline": "strength", "seed": f"s{i}"})
        titles.add(r.json()["title"])
    assert len(titles) >= 3  # le seed produit de la variété


# ---------- Persistance des séances générées ----------
def test_save_generated_session_planned(client):
    gen = client.post("/generate", json={"discipline": "strength", "seed": "save1"}).json()
    r = client.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2028-02-10",
        "duration_min": gen["duration_min"], "title": gen["title"],
        "status": "planned", "detail": gen})
    assert r.status_code == 200
    assert r.json()["persisted_status"] == "planned"
    # visible dans l'historique
    rows = client.get("/sessions/recent?n=80").json()["sessions"]
    saved = next(s for s in rows if s["session_date"] == "2028-02-10")
    assert saved["status"] == "planned"
    assert saved["discipline"] == "strength"


def test_save_generated_session_appears_in_agenda(client):
    gen = client.post("/generate", json={"discipline": "run", "seed": "save2"}).json()
    # 2028-02-07 est un lundi → l'agenda de cette semaine doit montrer la séance
    client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2028-02-07",
        "duration_min": 60, "title": gen["title"], "status": "planned", "detail": gen})
    week = client.post("/agenda/week", json={"date": "2028-02-07"}).json()
    mon = next(d for d in week["days"] if d["date"] == "2028-02-07")
    assert mon["done"] is not None
    assert mon["done"]["discipline"] == "run"
    assert mon["done"]["status"] == "planned"


def test_save_done_computes_load(client):
    r = client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2028-03-15",
        "duration_min": 60, "intensity_rpe": 7, "status": "done"})
    assert r.status_code == 200
    rows = client.get("/sessions/recent?n=80").json()["sessions"]
    saved = next(s for s in rows if s["session_date"] == "2028-03-15")
    assert saved["status"] == "done"
    assert saved["stress_units"] == pytest.approx(29.4, abs=0.5)


# ---------- Générateur Run (Mission 2) ----------
def test_run_generate_detail(client):
    r = client.get("/generate/run?type=vma_courte&seed=1")
    assert r.status_code == 200
    s = r.json()
    assert s["type"] == "vma_courte"
    assert s["seed"] == "vma_courte_001"
    assert s["body"] and s["body"][0]["pace_min_km"]
    assert s["body"][0]["pct_vma"] in (100, 105, 110)
    assert s["calories"] > 0


def test_run_generate_deterministic(client):
    a = client.get("/generate/run?type=seuil&seed=12").json()
    b = client.get("/generate/run?type=seuil&seed=12").json()
    assert a == b


def test_run_generate_unique_first_100(client):
    import json as _json
    sigs = {_json.dumps(client.get(f"/generate/run?type=tempo&seed={n}").json(), sort_keys=True)
            for n in range(1, 101)}
    assert len(sigs) == 100   # aucune répétition sur les 100 premières


def test_run_generate_bad_type(client):
    assert client.get("/generate/run?type=marathon&seed=1").status_code == 422


def test_run_library(client):
    lib = client.get("/generate/run/library").json()
    assert lib["total"] == 700
    assert len(lib["library"]["vma_longue"]) == 100


def test_run_generate_custom_vma(client):
    # VMA réelle différente → allures recalculées
    s = client.get("/generate/run?type=vma_courte&seed=1&vma=16&fcmax=190").json()
    assert s["body"][0]["pace_kmh"] >= 16.0  # 100% de 16 km/h


# ---------- Plan glissant détaillé (Mission 1B) ----------
def test_weekly_plan_structure(client):
    p = client.get("/plan/weekly?from_week=0&n=6").json()
    assert len(p["weeks"]) == 6
    w0 = p["weeks"][0]
    assert w0["week_type"] == "big_work"   # semaine du 15/06 = grande
    assert len(w0["days"]) == 7
    # jour OFF (mer) = double séance ; détail run présent
    wed = next(d for d in w0["days"] if d["day_of_week"] == "wed")
    assert wed["is_work_day"] is False
    assert len(wed["sessions"]) == 2
    run = next(s for s in wed["sessions"] if s["type"] == "run")
    assert run["detail"]["body"][0]["pace_min_km"]


def test_weekly_plan_strength_progresses(client):
    # semaine 0 → 5/3/1 S1 ; semaine 2 → S3
    p = client.get("/plan/weekly?from_week=0&n=3").json()
    s0 = next(s for d in p["weeks"][0]["days"] for s in d["sessions"] if s["type"] == "strength")
    s2 = next(s for d in p["weeks"][2]["days"] for s in d["sessions"] if s["type"] == "strength")
    assert s0["detail"]["week"] == 1
    assert s2["detail"]["week"] == 3


def test_weekly_plan_sunday_small_week_is_swim(client):
    # semaine 1 (22/06) = petite semaine → dimanche natation
    p = client.get("/plan/weekly?from_week=1&n=1").json()
    sun = next(d for d in p["weeks"][0]["days"] if d["day_of_week"] == "sun")
    assert any(s["type"] == "swim" for s in sun["sessions"])


# ---------- Générateur WOD (Mission 3) ----------
def test_wod_generate_deterministic(client):
    a = client.post("/generate/wod", json={"format": "amrap", "duration_min": 12, "seed": "z"}).json()
    b = client.post("/generate/wod", json={"format": "amrap", "duration_min": 12, "seed": "z"}).json()
    assert a == b
    assert a["description"] and a["target_score"] and a["name"]


def test_wod_exclude_lumbar_by_default(client):
    # sur tous les formats, exclude_lumbar=ON → jamais de mouvement lombaire
    for fmt in ["amrap", "for_time", "emom", "chipper", "rft", "ladder", "death_by_emom"]:
        for i in range(8):
            w = client.post("/generate/wod", json={"format": fmt, "seed": f"k{i}"}).json()
            assert w["lumbar_safe"] is True


def test_wod_auto_and_random(client):
    auto = client.post("/generate/wod", json={"format": "auto", "seed": "a"}).json()
    assert auto["format_key"] in [
        "amrap", "for_time", "emom", "death_by", "death_by_emom", "chipper",
        "buy_in_amrap_buy_out", "pyramid_asc", "pyramid_desc", "pyramid_full",
        "multi_amrap_blocks", "rft", "tabata", "amrap_score_double", "ladder"]
    rnd = client.get("/generate/wod/random").json()
    assert rnd["description"]


def test_wod_variety(client):
    names = {client.post("/generate/wod", json={"format": "for_time", "seed": f"s{i}"}).json()["name"]
             for i in range(12)}
    assert len(names) >= 8


def test_wod_duration_bounds(client):
    assert client.post("/generate/wod", json={"duration_min": 99}).status_code == 422


# ---------- Force 5/3/1 (Mission 4) ----------
def test_strength_531_loads(client):
    s = client.get("/generate/strength?day=push&week=3&cycle=0").json()
    assert s["day"] == "push"
    assert s["main_lift"]["name"] == "Développé couché"
    assert s["main_lift"]["training_max"] == 90.0   # 1RM ~100, objectif 140
    # S3 = 75/85/95% du TM 90 → 67.5/77.5/85 (arrondi 2,5 kg)
    loads = [x["load_kg"] for x in s["main_lift"]["sets"]]
    assert loads == [67.5, 77.5, 85.0]
    assert s["main_lift"]["sets"][-1]["amrap"] is True
    # Big 3 McGill + finisher non lombaire
    assert s["warmup_mcgill"]
    assert s["finisher_wod"]["lumbar_safe"] is True


def test_strength_531_cycle_progression(client):
    c0 = client.get("/strength/cycle?cycle=0").json()["training_max"]
    c2 = client.get("/strength/cycle?cycle=2").json()["training_max"]
    assert c2["bench"] == c0["bench"] + 5    # +2.5/cycle haut du corps
    assert c2["squat"] == c0["squat"] + 10   # +5/cycle bas du corps


def test_strength_531_pull_has_gtg(client):
    s = client.get("/generate/strength?day=pull&week=1").json()
    assert "grease_the_groove" in s


def test_strength_531_deload(client):
    s = client.get("/generate/strength?day=legs&week=4").json()
    assert s["is_deload"] is True
    assert [x["pct_tm"] for x in s["main_lift"]["sets"]] == [50, 60, 70]


def test_strength_531_bad_day(client):
    assert client.get("/generate/strength?day=arms").status_code == 422


def test_strength_progression(client):
    p = client.get("/strength/progression?lift=bench&cycles=6").json()
    assert p["name"] == "Développé couché"
    assert len(p["points"]) == 6
    # charge croissante de cycle en cycle
    loads = [x["top_set_kg"] for x in p["points"]]
    assert loads == sorted(loads) and loads[-1] > loads[0]
    assert client.get("/strength/progression?lift=biceps").status_code == 422


# ---------- Plan annuel (Mission 1) ----------
def test_plan_annual_structure(client):
    body = client.get("/plan/annual").json()
    assert body["goal_date"] == "2029-03-01"
    assert body["weeks_total"] >= 130
    assert body["blocks"]
    first = body["blocks"][0]
    assert first["phase"] == "BASE"
    assert first["week_start"] == 0
    assert "volume_su_grande_semaine" in first
    assert "dominante" in first
    # jalons benchmarks + sélection finale
    assert any("SÉLECTION" in m["label"] for m in body["milestones"])
    # blocs contigus
    for a, b in zip(body["blocks"], body["blocks"][1:]):
        assert b["week_start"] == a["week_end"] + 1


# ---------- Roadmap (plan annuel) ----------
def test_roadmap_to_selection(client):
    r = client.post("/roadmap", json={"weeks_to_selection": 142, "current_week": 0})
    assert r.status_code == 200
    body = r.json()
    assert body["selection_week"] == 142
    assert body["current_phase"] == "base"
    assert body["blocks"][0]["week_start"] == 0
    assert any(b["is_current"] for b in body["blocks"])
    assert any("SÉLECTION" in m for m in body["milestones"])


def test_roadmap_rejects_out_of_range(client):
    assert client.post("/roadmap", json={"weeks_to_selection": 3}).status_code == 422


# ---------- Analytics ----------
def test_analytics_warming_up_then_clear(client):
    snap = client.get("/analytics/snapshot").json()
    assert "status" in snap
    # alimente assez de données puis re-teste
    for i in range(5):
        d = f"2026-05-0{i + 1}"
        client.post("/sessions/complete", json={
            "discipline": "run", "session_date": d, "duration_min": 55,
            "intensity_rpe": 6, "stress_units": 50})
        client.post("/metrics/record", json={"date": d, "readiness": 70, "fatigue": 35})
    snap2 = client.get("/analytics/snapshot").json()
    assert snap2["status"] != "warming_up"
    assert 0 <= snap2["readiness"] <= 100
    assert snap2["acwr"] >= 0


# ---------- Historique ----------
def test_sessions_recent(client):
    client.post("/sessions/complete", json={
        "discipline": "swim", "session_date": "2026-06-14",
        "duration_min": 40, "intensity_rpe": 4})
    body = client.get("/sessions/recent?n=10").json()
    assert any(s["discipline"] == "swim" for s in body["sessions"])


# ---------- Boucle adaptative ----------
def test_session_su_computed_on_completion(client):
    r = client.post("/sessions/complete", json={
        "discipline": "run", "session_date": "2027-03-01",
        "duration_min": 60, "intensity_rpe": 7})
    assert r.status_code == 200
    # 60 × (7/10)² = 29.4 SU stockées (pas 0)
    rows = client.get("/sessions/recent?n=50").json()["sessions"]
    sess = next(s for s in rows if s["session_date"] == "2027-03-01")
    assert sess["stress_units"] == pytest.approx(29.4, abs=0.5)


def test_session_injects_history_context(client):
    # semaine chargée avant la date cible → budget consommé non nul + disciplines récentes
    for d, disc in [("2027-04-05", "run"), ("2027-04-06", "strength"),
                    ("2027-04-07", "crossfit")]:
        client.post("/sessions/complete", json={
            "discipline": disc, "session_date": d,
            "duration_min": 60, "intensity_rpe": 8})
    r = client.post("/coach/session", json={
        "date": "2027-04-08", "readiness": 70, "fatigue": 45, "sleep_quality": 70})
    assert r.status_code == 200
    ctx = r.json()["context"]
    assert ctx["budget_consumed_pct"] > 0
    assert ctx["days_since_rest"] >= 3
    assert ctx["last_two_disciplines"]  # rempli depuis l'historique
    assert "acwr" in ctx


def test_session_explicit_context_overrides_history(client):
    r = client.post("/coach/session", json={
        "date": "2027-04-08", "readiness": 70, "fatigue": 45, "sleep_quality": 70,
        "budget_consumed_pct": 95, "days_since_rest": 1})
    ctx = r.json()["context"]
    assert ctx["budget_consumed_pct"] == 95   # la valeur client prime
    assert ctx["days_since_rest"] == 1


# ---------- Garmin Connect (OAuth serveur) ----------
def test_garmin_status_not_configured(client):
    body = client.get("/garmin/status").json()
    assert body["configured"] is False
    assert body["connected"] is False


def test_garmin_connect_requires_config(client):
    assert client.get("/garmin/connect").status_code == 503


def test_garmin_sync_requires_connection(client):
    assert client.post("/garmin/sync").status_code == 400


def test_garmin_token_roundtrip_and_disconnect(client):
    import api.main as m
    aid = m.store.athlete_id
    m.garmin_tokens.save_request_token(aid, "req-tok", "req-sec")
    m.garmin_tokens.save_access_token(aid, "acc-tok", "acc-sec")
    assert client.get("/garmin/status").json()["connected"] is True
    assert m.garmin_tokens.get(aid)["request_token"] is None  # nettoyé après échange
    assert client.post("/garmin/disconnect").json()["status"] == "disconnected"
    assert client.get("/garmin/status").json()["connected"] is False


def test_garmin_map_to_metrics():
    from api.garmin import map_to_metrics
    out = map_to_metrics({
        "dailies": [{"restingHeartRateInBeatsPerMinute": 46}],
        "sleeps": [{"durationInSeconds": 27000}],   # 7.5 h
        "hrv": [{"lastNightAvg": 72}]})
    assert out["resting_hr"] == 46
    assert out["sleep_hours"] == 7.5
    assert out["hrv"] == 72.0
    assert map_to_metrics({}) == {}   # aucune donnée → rien à écrire


# ---------- Coach ----------
def test_daily_decision_nominal(client):
    r = client.post("/coach/daily-decision", json={
        "day_of_week": "wed", "is_work_day": False, "week_type": "big_work",
        "readiness": 75, "fatigue": 35, "sleep_quality": 80})
    assert r.status_code == 200
    body = r.json()
    assert body["best_action"]
    assert 0 < body["duration_min"] <= 240
    assert 0 <= body["intensity_cap"] <= 10


def test_daily_decision_sciatic_flare_is_protective(client):
    r = client.post("/coach/daily-decision", json={
        "day_of_week": "mon", "is_work_day": True, "week_type": "big_work",
        "readiness": 90, "fatigue": 10, "sleep_quality": 90,
        "sciatic_flare": True})
    assert r.status_code == 200
    body = r.json()
    # Jamais de séance lourde pendant une crise sciatique
    assert body["intensity_cap"] <= 6
    assert body["safety_notes"]


def test_daily_decision_rejects_bad_day(client):
    r = client.post("/coach/daily-decision", json={
        "day_of_week": "lundi", "is_work_day": True, "week_type": "big_work",
        "readiness": 75, "fatigue": 35, "sleep_quality": 80})
    assert r.status_code == 422


def test_weekly_budget(client):
    r = client.post("/coach/weekly-budget", json={
        "week_type": "small_work",
        "sessions": [{"discipline": "run", "duration_min": 60, "intensity": 6}]})
    assert r.status_code == 200
    body = r.json()
    assert body["budget_su"] > 0
    assert body["remaining_su"] <= body["budget_su"]


def test_arbitrate_goals(client):
    r = client.post("/coach/arbitrate-goals", json={"goals": [
        {"goal_id": "raid", "name": "Sélection RAID", "discipline": "crossfit",
         "target_date_weeks": 140, "priority": 1},
        {"goal_id": "semi", "name": "Semi 1h35", "discipline": "run",
         "target_date_weeks": 30, "priority": 2}]})
    assert r.status_code == 200
    body = r.json()
    assert body["primary_goal_id"] in {"raid", "semi"}
    assert set(body["ranked_goal_ids"]) == {"raid", "semi"}


# ---------- Run ----------
def test_hr_profile_tanaka_default(client):
    r = client.post("/run/hr-profile", json={"age": 31})
    assert r.status_code == 200
    body = r.json()
    assert body["fc_max"] == pytest.approx(208 - 0.7 * 31, abs=2)
    assert len(body["zones"]) >= 4


def test_run_predictions(client):
    r = client.post("/run/predictions", json={"distance_km": 8, "time_sec": 2400})
    assert r.status_code == 200
    body = r.json()
    assert 10 < body["vma_estimate_kmh"] < 20
    assert body["predictions"]


def test_pace_table_terrain(client):
    r = client.post("/run/pace-table", json={
        "vma_kmh": 14, "terrain": "trail", "elevation_gain_m_per_km": 30,
        "load_kg": 10})
    assert r.status_code == 200
    assert r.json()["targets"]


def test_pace_table_rejects_unknown_terrain(client):
    r = client.post("/run/pace-table", json={"vma_kmh": 14, "terrain": "moon"})
    assert r.status_code == 422


# ---------- Strength ----------
def test_strength_generate(client):
    r = client.post("/strength/generate", json={
        "recovery_score": 80, "sleep_quality": 75, "seed": "test-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["blocks"]
    assert body["duration_min"] > 0


def test_pr_estimate_epley(client):
    r = client.post("/strength/pr-estimate", json={
        "movement_id": "bench_press", "weight_kg": 90, "reps": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["e1rm"] > 90
    assert body["rm5"] <= body["rm3"] <= body["e1rm"]


def test_raid_strength_report_matches_known_profile(client):
    r = client.post("/raid/strength-report", json={
        "current": {"pullups_max": 16, "pushups_max": 60, "dips_max": 40,
                    "leg_raises_max": 18, "rope_climb_5m": 1, "cooper_m": 2850},
        "bodyweight_kg": 75, "tier": "elite"})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["global_readiness_pct"] <= 100
    assert body["targets"]


# ---------- Plans ----------
def test_auto_plan(client):
    r = client.post("/plans/auto-generate", json={
        "goal_type": "raid", "goal_name": "RAID 2029",
        "duration_weeks": 16, "analytics": {}})
    assert r.status_code == 200
    assert r.json()["duration_weeks"] == 16


# ---------- Nutrition ----------
def test_daily_macros(client):
    r = client.post("/nutrition/daily-macros", json={
        "weight_kg": 75, "height_cm": 172, "age": 31})
    assert r.status_code == 200
    body = r.json()
    assert body["protein_g"] >= 150  # recomp : 2,2 g/kg minimum
    assert body["calories"] > 1500


def test_selection_day(client):
    r = client.post("/nutrition/selection-day", json={"weight_kg": 75})
    assert r.status_code == 200
    assert r.json()["morning"]


# ---------- Nutrition+ ----------
def test_nutrition_supplements(client):
    s = client.get("/nutrition/supplements?session_type=strength").json()
    names = [it["name"] for g in s["groups"] for it in g["items"]]
    assert any("Créatine" in n for n in names)
    assert any("Collagène" in n for n in names)


def test_nutrition_foods_and_synergies(client):
    foods = client.get("/nutrition/foods").json()["foods"]
    assert any(f["id"] == "poulet" for f in foods)
    syn = client.get("/nutrition/synergies").json()
    assert syn["synergies"] and syn["anti_synergies"]


def test_nutrition_portions(client):
    r = client.post("/nutrition/portions", json={
        "target_p": 165, "target_c": 300, "target_f": 55}).json()
    assert r["items"]
    # totaux protéines proches de la cible (±15%)
    assert 140 <= r["totals"]["p"] <= 190


def test_nutrition_guardrails_alerts(client):
    g = client.post("/nutrition/guardrails", json={
        "weight_kg": 75, "calories": 1800, "protein_g": 120, "fat_g": 40}).json()["guardrails"]
    codes = {x["code"]: x["level"] for x in g}
    assert codes["lipides"] == "alert"       # 40 < 60 (0,8×75)
    assert codes["proteines"] == "alert"     # 120 < 135 (1,8×75)
    assert codes["red_s"] in ("warn", "alert")


# ---------- Persistance (nouveaux endpoints) ----------
def test_metrics_record_and_latest(client):
    r = client.post("/metrics/record", json={
        "date": "2026-06-12", "readiness": 72, "fatigue": 40,
        "sleep_quality": 70, "sciatic_flare": True})
    assert r.status_code == 200
    latest = client.get("/metrics/latest").json()
    assert latest["metric_date"] == "2026-06-12"
    assert latest["sciatic_flare"] == 1


def test_metrics_record_wearable_fields(client):
    # HRV / FC repos / heures de sommeil venant du wearable
    r = client.post("/metrics/record", json={
        "date": "2026-06-20", "readiness": 80, "fatigue": 25,
        "sleep_quality": 82, "sleep_hours": 7.5, "hrv": 68, "resting_hr": 47})
    assert r.status_code == 200
    latest = client.get("/metrics/latest").json()
    assert latest["hrv"] == 68
    assert latest["resting_hr"] == 47
    assert latest["sleep_hours"] == 7.5


def test_metrics_record_upsert_same_day(client):
    # date volontairement postérieure → garantie d'être la plus récente,
    # indépendamment de l'ordre d'exécution des autres tests
    client.post("/metrics/record", json={"date": "2031-01-01", "readiness": 50})
    client.post("/metrics/record", json={"date": "2031-01-01", "readiness": 65})
    latest = client.get("/metrics/latest").json()
    assert latest["metric_date"] == "2031-01-01"
    assert latest["readiness"] == 65


def test_metrics_record_rejects_bad_date(client):
    r = client.post("/metrics/record", json={"date": "12/06/2026"})
    assert r.status_code == 422


def test_session_complete(client):
    r = client.post("/sessions/complete", json={
        "discipline": "run", "session_date": "2026-06-12",
        "duration_min": 45, "intensity_rpe": 6, "stress_units": 45,
        "feedback": {"rpe_felt": 6}})
    assert r.status_code == 200
    assert r.json()["session_id"] >= 1


def test_session_rejects_unknown_discipline(client):
    r = client.post("/sessions/complete", json={
        "discipline": "yoga", "session_date": "2026-06-12",
        "duration_min": 45, "intensity_rpe": 6})
    assert r.status_code == 422


def test_benchmark_record_and_progression(client):
    # id dédié pour ne pas heurter les benchmarks seedés du profil
    for day, val in [("2026-06-01", 30), ("2026-06-12", 33)]:
        r = client.post("/benchmarks/record", json={
            "benchmark_id": "bench_test_progression", "result_value": val,
            "result_unit": "reps", "test_date": day})
        assert r.status_code == 200
    prog = client.get("/benchmarks/bench_test_progression/progression").json()
    values = [p["result_value"] for p in prog["results"]]
    assert values == [30, 33]


# ---------- Score WOD : suivi + analyse de performance ----------
def _save_done_wod(client, date, mode, *, time_sec=None, reps=None, cap_sec=720, capped=False):
    label = (f"{time_sec // 60:02d}:{time_sec % 60:02d}" if mode == "for_time"
             else f"{reps} reps/rounds")
    result = {"mode": mode, "time_sec": time_sec or cap_sec, "reps": reps or 0,
              "capped": capped, "cap_sec": cap_sec}
    return client.post("/sessions/save", json={
        "discipline": "crossfit", "session_date": date,
        "duration_min": max(1, (time_sec or cap_sec) // 60), "intensity_rpe": 9,
        "title": f"WOD test — {label}", "status": "done",
        "detail": {"name": "WOD test", "result": result, "score_label": label}})


def test_wod_score_surfaced_in_recent(client):
    _save_done_wod(client, "2028-07-03", "for_time", time_sec=510, cap_sec=900)
    rows = client.get("/sessions/recent?n=120").json()["sessions"]
    wod = next(s for s in rows if s["session_date"] == "2028-07-03")
    assert wod["status"] == "done"
    assert float(wod["stress_units"]) > 0          # le temps compte dans la charge
    assert wod["score"]["type"] == "time"
    assert wod["score"]["value"] == 510
    assert wod["score"]["label"] == "08:30"


def test_wod_score_label_in_agenda(client):
    # 2028-07-03 est un lundi
    week = client.post("/agenda/week", json={"date": "2028-07-03"}).json()
    mon = next(d for d in week["days"] if d["date"] == "2028-07-03")
    assert mon["done"]["score_label"] == "08:30"


def test_analytics_uses_wod_performance(client):
    # readiness pour débloquer l'analytics
    for day, r in [("2028-08-01", 70), ("2028-08-02", 72), ("2028-08-03", 68)]:
        client.post("/metrics/record", json={"date": day, "readiness": r, "fatigue": 30})
    # 3 WOD For Time chronométrés → la perf vient des WOD, pas du proxy readiness
    _save_done_wod(client, "2028-08-01", "for_time", time_sec=400, cap_sec=900)
    _save_done_wod(client, "2028-08-02", "for_time", time_sec=420, cap_sec=900)
    _save_done_wod(client, "2028-08-03", "for_time", time_sec=380, cap_sec=900)
    snap = client.get("/analytics/snapshot").json()
    assert snap["status"] != "warming_up"
    assert snap["performance_source"] == "wod"
    assert snap["wods_scored"] >= 3
    assert isinstance(snap["performance"], (int, float))


def test_wod_performance_fast_beats_capped():
    from api.main import _wod_performance
    fast = _wod_performance({"mode": "for_time", "time_sec": 300, "cap_sec": 900, "capped": False}, None)
    slow = _wod_performance({"mode": "for_time", "time_sec": 870, "cap_sec": 900, "capped": False}, None)
    capped = _wod_performance({"mode": "for_time", "time_sec": 900, "cap_sec": 900, "capped": True}, None)
    assert fast > slow > capped
    # AMRAP : battre son meilleur score → perf plus haute
    assert (_wod_performance({"mode": "amrap", "reps": 200}, 100.0)
            > _wod_performance({"mode": "amrap", "reps": 80}, 100.0))


# ---------- Cohérence /plan/day ↔ /plan/weekly (même séance pour un jour) ----------
def test_plan_day_matches_weekly(client):
    # 2026-06-24 (mercredi) — semaine du 15/06 = grande semaine (ancre)
    day = client.get("/plan/day?date=2026-06-24").json()
    assert day["date"] == "2026-06-24"
    assert day["sessions"], "le jour doit avoir au moins une séance"
    # même date via /plan/weekly (semaine 0 depuis l'ancre)
    wk = client.get("/plan/weekly?from_week=0&n=2").json()
    wday = next(d for w in wk["weeks"] for d in w["days"] if d["date"] == "2026-06-24")
    # titres + détails identiques (mêmes générateurs, mêmes seeds)
    assert [s["title"] for s in day["sessions"]] == [s["title"] for s in wday["sessions"]]
    assert day["sessions"][0]["detail"] == wday["sessions"][0]["detail"]


def test_plan_day_deterministic_across_weeks(client):
    # déterministe : deux appels pour la même date donnent la même séance
    a = client.get("/plan/day?date=2026-07-15").json()
    b = client.get("/plan/day?date=2026-07-15").json()
    assert a == b


def test_plan_day_validation(client):
    assert client.get("/plan/day?date=15-07-2026").status_code == 422
