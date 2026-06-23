"""Auth multi-utilisateurs : inscription (1er=propriétaire, puis code
d'invitation), connexion, jeton, et ISOLATION stricte des données entre
comptes. Vérifie aussi la compat mono-utilisateur (anonyme = propriétaire)."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["RAID_COACH_DB"] = ":memory:"
os.environ.pop("AUTH_REQUIRED", None)

from api import auth as _auth  # noqa: E402
import api.persistence  # noqa: E402
import api.main  # noqa: E402

importlib.reload(api.persistence)
importlib.reload(api.main)


@pytest.fixture(scope="module")
def client() -> TestClient:
    # Store/app frais et isolé pour ce module (les autres fichiers de test
    # rechargent le même singleton api.main et écriraient dans le même store
    # :memory: → on recharge ici pour des assertions déterministes).
    importlib.reload(api.persistence)
    importlib.reload(api.main)
    return TestClient(api.main.app)


def _bearer(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


# ---------- Primitives ----------
def test_password_hash_roundtrip():
    h = _auth.hash_password("s3cret-pass")
    assert _auth.verify_password("s3cret-pass", h)
    assert not _auth.verify_password("wrong", h)


def test_token_roundtrip_and_tamper():
    tok = _auth.make_token(42, "secretA")
    assert _auth.verify_token(tok, "secretA") == 42
    assert _auth.verify_token(tok, "secretB") is None       # mauvaise clé
    assert _auth.verify_token(tok + "x", "secretA") is None  # altéré


# ---------- Flux d'inscription ----------
def test_first_register_becomes_owner_with_existing_data(client):
    # le profil primaire est pré-seedé (données réelles : pullups_max=16)
    r = client.post("/auth/register", json={"email": "rick@example.com", "password": "motdepasse1"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["is_owner"] is True
    # le propriétaire récupère le profil existant
    me = client.get("/profile", headers=_bearer(body["token"])).json()
    assert me["current"].get("pullups_max") == 16


def test_second_register_requires_invite_code(client, monkeypatch):
    # sans code configuré → fermé
    monkeypatch.delenv("INVITE_CODE", raising=False)
    assert client.post("/auth/register", json={"email": "a@b.com", "password": "password1"}).status_code == 403
    # avec mauvais code → refus
    monkeypatch.setenv("INVITE_CODE", "RAID2029")
    assert client.post("/auth/register", json={
        "email": "a@b.com", "password": "password1", "invite_code": "x"}).status_code == 403
    # bon code → créé
    r = client.post("/auth/register", json={
        "email": "ami@b.com", "password": "password1", "invite_code": "RAID2029", "name": "Ami"})
    assert r.status_code == 200 and r.json()["user"]["is_owner"] is False


def test_login_and_me(client):
    r = client.post("/auth/login", json={"email": "rick@example.com", "password": "motdepasse1"})
    assert r.status_code == 200
    me = client.get("/auth/me", headers=_bearer(r.json()["token"])).json()
    assert me["user"]["email"] == "rick@example.com" and me["user"]["is_owner"] is True
    # mauvais mot de passe
    assert client.post("/auth/login", json={"email": "rick@example.com", "password": "bad"}).status_code == 401


def test_duplicate_email_rejected(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "RAID2029")
    assert client.post("/auth/register", json={
        "email": "rick@example.com", "password": "password1", "invite_code": "RAID2029"}).status_code == 409


# ---------- ISOLATION des données entre comptes ----------
def test_data_isolation_between_users(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "RAID2029")
    owner = client.post("/auth/login", json={"email": "rick@example.com", "password": "motdepasse1"}).json()["token"]
    friend = client.post("/auth/register", json={
        "email": "friend2@b.com", "password": "password1", "invite_code": "RAID2029"}).json()["token"]

    # chacun enregistre une métrique différente
    client.post("/metrics/record", json={"date": "2027-01-10", "readiness": 90}, headers=_bearer(owner))
    client.post("/metrics/record", json={"date": "2027-01-10", "readiness": 40}, headers=_bearer(friend))

    assert client.get("/metrics/latest", headers=_bearer(owner)).json()["readiness"] == 90
    assert client.get("/metrics/latest", headers=_bearer(friend)).json()["readiness"] == 40

    # une séance du propriétaire n'apparaît pas chez l'ami
    client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2027-01-11", "duration_min": 50,
        "title": "Footing proprio", "status": "done"}, headers=_bearer(owner))
    friend_sessions = client.get("/sessions/recent", headers=_bearer(friend)).json()["sessions"]
    assert all(s.get("family_id") != "Footing proprio" for s in friend_sessions)
    # le nouvel ami a un profil vierge (pas les maxes du proprio)
    assert client.get("/profile", headers=_bearer(friend)).json().get("current", {}).get("pullups_max") is None


def test_anonymous_falls_back_to_owner_when_not_enforced(client):
    # AUTH_REQUIRED non défini → un appel sans jeton renvoie les données du proprio
    r = client.get("/profile")
    assert r.status_code == 200
    assert r.json()["current"].get("pullups_max") == 16


# ---------- Rythme de travail par utilisateur (plan adapté) ----------
def test_per_user_weekly_schedule(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "RAID2029")
    tok = client.post("/auth/register", json={
        "email": "weekly@b.com", "password": "password1", "invite_code": "RAID2029"}).json()["token"]
    H = _bearer(tok)
    # rythme hebdo : entraînement lun/mer/ven uniquement
    client.patch("/profile", json={"work_schedule": {
        "type": "weekly", "training_days": ["mon", "wed", "fri"]}}, headers=H)
    # 2026-06-22 = lundi (entraînement), 2026-06-23 = mardi (repos)
    mon = client.get("/plan/day?date=2026-06-22", headers=H).json()
    tue = client.get("/plan/day?date=2026-06-23", headers=H).json()
    assert mon["week_type"] == "weekly"
    assert len(mon["sessions"]) >= 1          # lundi : séance
    assert tue["sessions"] == []              # mardi : repos


def test_per_user_opposite_police_phase(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "RAID2029")
    tok = client.post("/auth/register", json={
        "email": "police2@b.com", "password": "password1", "invite_code": "RAID2029"}).json()["token"]
    H = _bearer(tok)
    # phase opposée au propriétaire : ancre décalée d'une semaine
    client.patch("/profile", json={"work_schedule": {
        "type": "police_3223", "anchor_big_week_monday": "2026-06-22"}}, headers=H)
    # semaine du 15/06 : propriétaire = grande ; cet utilisateur = petite (ancre 22/06)
    wk = client.get("/plan/day?date=2026-06-15", headers=H).json()
    assert wk["week_type"] == "small_work"
