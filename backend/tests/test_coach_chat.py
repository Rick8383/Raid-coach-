"""Tests du Coach Chat (moteur déterministe) + endpoint /coach/chat, et
régression de l'agenda : une séance marquée 'done' l'emporte sur une 'planned'
le même jour (bug « marquer comme fait » non reflété dans l'agenda)."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["RAID_COACH_DB"] = ":memory:"

from engines.coach_chat import answer, detect_topic, RPE_SCALE  # noqa: E402

import api.persistence  # noqa: E402
import api.main  # noqa: E402

importlib.reload(api.persistence)
importlib.reload(api.main)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(api.main.app)


# ---------- Détection d'intention ----------
@pytest.mark.parametrize("msg,topic", [
    ("Qu'est-ce que je fais aujourd'hui ?", "today"),
    ("Explique-moi le RPE", "rpe"),
    ("C'est quoi une grande semaine ?", "schedule"),
    ("Combien de protéines par jour ?", "nutrition"),
    ("Comment progresser au développé couché ?", "strength"),
    ("Quelle allure pour mon footing ?", "run"),
    ("Différence entre AMRAP et For Time ?", "wod"),
    ("J'ai mal au dos, ma sciatique", "sciatica"),
    ("La sélection RAID 2029", "raid"),
    ("Bonjour", "help"),
])
def test_detect_topic(msg, topic):
    assert detect_topic(msg) == topic


def test_rpe_scale_complete():
    assert [r["value"] for r in RPE_SCALE] == list(range(1, 11))
    assert all(r["label"] and r["desc"] and r["zone"] for r in RPE_SCALE)


def test_answer_shape_and_personalisation():
    res = answer("Combien de protéines ?", {"profile": {"weight_kg": 75}})
    assert set(res) >= {"reply", "topic", "suggestions"}
    assert res["topic"] == "nutrition"
    assert "150" in res["reply"]  # 2 g/kg * 75
    assert isinstance(res["suggestions"], list) and res["suggestions"]


def test_answer_rpe_specific_number():
    res = answer("c'est quoi un rpe 8 ?")
    assert res["topic"] == "rpe"
    assert "8" in res["reply"]


def test_answer_fallback():
    res = answer("xyzzy blabla random")
    assert res["topic"] == "fallback"
    assert res["suggestions"]


# ---------- Endpoint ----------
def test_chat_endpoint(client):
    r = client.post("/coach/chat", json={"message": "Qu'est-ce que je fais aujourd'hui ?",
                                         "date": "2026-06-15"})
    assert r.status_code == 200
    body = r.json()
    assert body["topic"] == "today"
    assert "grande semaine" in body["reply"].lower()


def test_chat_endpoint_validation(client):
    assert client.post("/coach/chat", json={"message": ""}).status_code == 422


# ---------- Régression agenda : 'done' prioritaire sur 'planned' ----------
def test_agenda_done_beats_planned_same_day(client):
    # 2028-05-08 est un lundi. On planifie une course, puis on marque une séance
    # de force comme faite le même jour → l'agenda doit montrer la force 'done'.
    client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2028-05-08",
        "duration_min": 50, "title": "Footing", "status": "planned"})
    client.post("/sessions/save", json={
        "discipline": "strength", "session_date": "2028-05-08",
        "duration_min": 70, "title": "Force PUSH S1", "status": "done"})
    week = client.post("/agenda/week", json={"date": "2028-05-08"}).json()
    mon = next(d for d in week["days"] if d["date"] == "2028-05-08")
    assert mon["done"] is not None
    assert mon["done"]["status"] == "done"
    assert mon["done"]["discipline"] == "strength"
    assert mon["done"]["title"] == "Force PUSH S1"
