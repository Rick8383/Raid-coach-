"""Recalage de la PHASE du rythme 3/2/2/3 (POST /schedule/phase).

Cas réel (17/08/2026) : l'ancre stockée déclarait la semaine en cours comme
GRANDE (service lun/mar) alors que l'athlète était en PETITE semaine (service
mer/jeu). Recaler la phase doit corriger tout l'agenda SANS décaler la
progression 5/3/1.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from engines.schedule import user_schedule as us


@pytest.fixture()
def client() -> TestClient:
    import importlib
    from api import main as api_main
    importlib.reload(api_main)
    return TestClient(api_main.app)


MONDAY = "2026-08-17"      # lundi
WEDNESDAY = "2026-08-19"


def _set_anchor(client, anchor: str) -> None:
    client.patch("/profile", json={"work_schedule": {
        "type": "police_3223", "anchor_big_week_monday": anchor}})


def test_phase_switch_fixes_service_days(client):
    # Ancre = ce lundi déclaré GRANDE → lundi en service (symptôme constaté).
    _set_anchor(client, MONDAY)
    before = client.post("/schedule/day", json={"date": MONDAY}).json()
    assert before["week_type"] == "big_work" and before["is_work_day"] is True

    r = client.post("/schedule/phase",
                    json={"is_big_week": False, "reference_date": MONDAY})
    assert r.status_code == 200
    assert r.json()["week_type"] == "small_work"

    # Lundi/mardi deviennent OFF, mercredi/jeudi passent en service.
    mon = client.post("/schedule/day", json={"date": MONDAY}).json()
    wed = client.post("/schedule/day", json={"date": WEDNESDAY}).json()
    assert mon["week_type"] == "small_work" and mon["is_work_day"] is False
    assert wed["is_work_day"] is True


def test_phase_switch_preserves_531_progression(client):
    """Le J0 de la progression force ne bouge pas quand on recale le service."""
    _set_anchor(client, MONDAY)
    before = client.get(f"/plan/day?date={MONDAY}").json()["week_index"]

    client.post("/schedule/phase",
                json={"is_big_week": False, "reference_date": MONDAY})

    after = client.get(f"/plan/day?date={MONDAY}").json()["week_index"]
    assert after == before, "recaler la phase ne doit pas décaler le cycle 5/3/1"
    prof = client.get("/profile").json()
    assert prof["work_schedule"]["start_monday"] == MONDAY   # J0 figé
    assert prof["work_schedule"]["anchor_big_week_monday"] == "2026-08-10"


def test_phase_alternates_after_switch(client):
    """Après recalage, l'alternance repart correctement (S+1 = grande)."""
    _set_anchor(client, MONDAY)
    client.post("/schedule/phase",
                json={"is_big_week": False, "reference_date": MONDAY})
    nxt = client.post("/schedule/day", json={"date": "2026-08-24"}).json()
    prev = client.post("/schedule/day", json={"date": "2026-08-10"}).json()
    assert nxt["week_type"] == "big_work"
    assert prev["week_type"] == "big_work"


def test_phase_switch_is_idempotent(client):
    _set_anchor(client, MONDAY)
    a = client.post("/schedule/phase",
                    json={"is_big_week": False, "reference_date": MONDAY}).json()
    b = client.post("/schedule/phase",
                    json={"is_big_week": False, "reference_date": MONDAY}).json()
    assert a["week_type"] == b["week_type"] == "small_work"
    assert (a["profile"]["work_schedule"]["anchor_big_week_monday"]
            == b["profile"]["work_schedule"]["anchor_big_week_monday"])


def test_phase_rejected_for_weekly_rhythm(client):
    client.patch("/profile", json={"work_schedule": {
        "type": "weekly", "training_days": ["mon", "wed", "fri"]}})
    r = client.post("/schedule/phase", json={"is_big_week": False})
    assert r.status_code == 409


def test_plan_start_prefers_explicit_start_monday():
    """Découplage : start_monday explicite prime sur l'ancre (police)."""
    cfg = us.normalize({"type": "police_3223",
                        "anchor_big_week_monday": "2026-08-10",
                        "start_monday": "2026-08-17"})
    assert us.plan_start(cfg) == date(2026, 8, 17)
    # Sans start_monday : comportement historique (l'ancre est le J0).
    cfg2 = us.normalize({"type": "police_3223",
                         "anchor_big_week_monday": "2026-08-10"})
    assert us.plan_start(cfg2) == date(2026, 8, 10)
