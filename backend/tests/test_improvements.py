"""Améliorations 1-6 : 1RM auto, 80/20, plyo, tests RAID, sommeil, glucides auto."""
from datetime import date

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    import importlib
    from api import main as api_main
    importlib.reload(api_main)
    return TestClient(api_main.app)


# ---------- 1. Suggestion 1RM (autorégulation) ----------
def test_rm_suggestion_on_big_amrap(client):
    perf = {"lift": "Rowing barre", "est_1rm": 108.0, "sets": [
        {"reps": 6, "load_kg": 90, "top": True}]}
    r = client.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2028-04-03",
        "duration_min": 70, "intensity_rpe": 8, "status": "done",
        "title": "Force PULL — S1", "performed": perf}).json()
    sug = r["rm_suggestion"]
    assert sug is not None
    assert sug["lift_key"] == "row" and sug["estimated_1rm"] == 108.0
    # Après mise à jour du 1RM, la même perf ne déclenche plus de suggestion.
    client.post("/benchmarks/record", json={
        "benchmark_id": "row_1rm", "result_value": 110,
        "result_unit": "kg", "test_date": "2028-04-03"})
    r2 = client.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2028-04-10",
        "duration_min": 70, "intensity_rpe": 8, "status": "done",
        "title": "Force PULL — S2", "performed": perf}).json()
    assert r2["rm_suggestion"] is None


# ---------- 2. Distribution 80/20 ----------
def test_intensity_distribution_80_20(client):
    # 3 footings faciles (RPE 3) + 1 séance dure (RPE 8) → 75 % facile.
    for i, (rpe, day) in enumerate([(3, "03"), (3, "04"), (3, "05"), (8, "06")]):
        client.post("/sessions/save", json={
            "discipline": "run", "session_date": f"2028-04-{day}",
            "duration_min": 60, "intensity_rpe": rpe, "status": "done",
            "title": f"run 8020 {i}"})
    for d in ["03", "04", "05"]:
        client.post("/metrics/record", json={
            "date": f"2028-04-{d}", "readiness": 70, "fatigue": 30,
            "sleep_quality": 70})
    snap = client.get("/analytics/snapshot").json()
    dist = snap.get("intensity_distribution")
    assert dist is not None
    assert dist["low_pct"] == 75 and dist["target_low_pct"] == 80


# ---------- 3. Pliométrie + côtes sur le jour VMA courte ----------
def test_plyo_finisher_on_vma_day(client):
    from engines.weekly_plan import build_day
    # 2026-06-17 = mercredi semaine 0 (grande) → VMA courte au template.
    day = build_day(date(2026, 6, 17))
    run = next(s for s in day["sessions"] if s["type"] == "run")
    plyo = run["detail"].get("plyo_finisher")
    assert plyo and plyo["blocks"]
    assert any("côte" in b or "sprint" in b for b in plyo["blocks"])


# ---------- 4. Semaine de tests RAID (toutes les 6 semaines) ----------
def test_raid_test_battery_every_6_weeks(client):
    from engines.weekly_plan import build_day
    # plan_w % 6 == 5 → semaine 5 (0-based) : lundi 2026-07-20, dimanche 26/07.
    day = build_day(date(2026, 7, 26))
    titles = [s["title"] for s in day["sessions"]]
    assert any("TESTS RAID" in t for t in titles)
    test_s = next(s for s in day["sessions"] if "TESTS RAID" in s["title"])
    assert any("Cooper" in l for l in test_s["detail"]["description"])
    # Dimanche d'une semaine NON test → pas de batterie.
    day2 = build_day(date(2026, 7, 19))
    assert not any("TESTS RAID" in s["title"] for s in day2["sessions"])


# ---------- 5. Sommeil court → intensité plafonnée ----------
def test_short_sleep_caps_intensity(client):
    r = client.post("/coach/session", json={
        "readiness": 80, "fatigue": 20, "sleep_quality": 40,
        "sleep_hours": 5, "date": "2026-06-17"}).json()
    assert float(r["intensity_cap"]) <= 6.0
    assert any("Sommeil" in n for n in r.get("safety_notes", []))


# ---------- 6. Glucides auto-périodisés depuis le plan ----------
def test_carb_periodization_auto_from_plan(client):
    body = {"weight_kg": 80, "height_cm": 180, "age": 30}
    # Mercredi grande semaine = double séance (VMA + force) → high carb.
    hi = client.post("/nutrition/daily-macros", json={**body, "date": "2026-06-17"}).json()
    assert hi["auto_activity"]["activity"] == "high"
    assert hi["day_type"] == "high_carb"
    # Sans date → comportement historique (activity fourni/défaut), pas d'auto.
    manual = client.post("/nutrition/daily-macros", json={**body, "activity": "rest"}).json()
    assert manual.get("auto_activity") is None
    assert manual["day_type"] == "low_carb"
    assert hi["carbs_g"] > manual["carbs_g"]
