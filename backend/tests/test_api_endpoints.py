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


# ---------- Persistance (nouveaux endpoints) ----------
def test_metrics_record_and_latest(client):
    r = client.post("/metrics/record", json={
        "date": "2026-06-12", "readiness": 72, "fatigue": 40,
        "sleep_quality": 70, "sciatic_flare": True})
    assert r.status_code == 200
    latest = client.get("/metrics/latest").json()
    assert latest["metric_date"] == "2026-06-12"
    assert latest["sciatic_flare"] == 1


def test_metrics_record_upsert_same_day(client):
    client.post("/metrics/record", json={"date": "2026-06-13", "readiness": 50})
    client.post("/metrics/record", json={"date": "2026-06-13", "readiness": 65})
    latest = client.get("/metrics/latest").json()
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
