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


# ---------- Code d'invitation géré dans l'app par le propriétaire ----------
def test_owner_managed_invite_code(client, monkeypatch):
    monkeypatch.delenv("INVITE_CODE", raising=False)  # pas de code via env
    owner = client.post("/auth/login", json={
        "email": "rick@example.com", "password": "motdepasse1"}).json()["token"]
    # sans code défini → inscription fermée
    assert client.post("/auth/register", json={
        "email": "x1@b.com", "password": "password1"}).status_code == 403
    # le propriétaire définit le code dans l'app
    r = client.post("/auth/invite-code", json={"invite_code": "1995"}, headers=_bearer(owner))
    assert r.status_code == 200 and r.json()["invite_code"] == "1995"
    # un ami s'inscrit avec ce code
    assert client.post("/auth/register", json={
        "email": "pote@b.com", "password": "password1", "invite_code": "1995"}).status_code == 200
    # mauvais code → refus
    assert client.post("/auth/register", json={
        "email": "pote2@b.com", "password": "password1", "invite_code": "0000"}).status_code == 403
    # un non-propriétaire ne peut pas changer le code
    friend = client.post("/auth/login", json={"email": "pote@b.com", "password": "password1"}).json()["token"]
    assert client.post("/auth/invite-code", json={"invite_code": "hack"},
                       headers=_bearer(friend)).status_code == 403


def test_delete_session_isolated(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "1995")
    a = client.post("/auth/login", json={"email": "rick@example.com", "password": "motdepasse1"}).json()["token"]
    b = client.post("/auth/register", json={
        "email": "delfriend@b.com", "password": "password1", "invite_code": "1995"}).json()["token"]
    sid = client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2028-10-10", "duration_min": 30,
        "title": "Test", "status": "done"}, headers=_bearer(a)).json()["session_id"]
    # un autre utilisateur ne peut pas supprimer la séance de A
    assert client.delete(f"/sessions/{sid}", headers=_bearer(b)).status_code == 404
    # le propriétaire de la séance peut
    assert client.delete(f"/sessions/{sid}", headers=_bearer(a)).status_code == 200


# ---------- Full body, trap barre, team WOD, ratios auto ----------
def test_fullbody_style_in_plan(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "1995")
    tok = client.post("/auth/register", json={
        "email": "fb@b.com", "password": "password1", "invite_code": "1995"}).json()["token"]
    H = _bearer(tok)
    client.patch("/profile", json={"work_schedule": {
        "type": "police_3223", "anchor_big_week_monday": "2026-06-15",
        "training_style": "fullbody"}}, headers=H)
    # 2026-06-15 lundi grande semaine = jour de force (push en split) → full body
    s531 = client.get("/generate/strength?day=fullbody", headers=H).json()
    assert len(s531["main_lifts"]) == 3   # squat + DC + rowing
    # le plan du jour propose une séance FULL BODY (2026-06-15 = lundi = jour force)
    day = client.get("/plan/day?date=2026-06-15", headers=H).json()
    strength = [s for s in day["sessions"] if s["type"] == "strength"]
    assert strength and "FULL BODY" in strength[0]["title"]
    assert strength[0]["duration_min"] <= 75
    assert len(strength[0]["detail"]["main_lifts"]) == 3


def test_trap_bar_in_legs(client):
    s = client.get("/generate/strength?day=legs").json()
    names = [a["name"] for a in s["accessories"]]
    assert any("trap-barre" in n.lower() for n in names)


def test_team_wod(client):
    w = client.post("/generate/wod", json={
        "format": "amrap", "duration_min": 12, "seed": "team1", "team_size": 3}).json()
    assert w["team_size"] == 3
    assert "TEAM ×3" in w["format"]
    assert any("ÉQUIPE DE 3" in line for line in w["description"])


def test_ratio_autofilled_from_1rm(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "1995")
    tok = client.post("/auth/register", json={
        "email": "ratio@b.com", "password": "password1", "invite_code": "1995"}).json()["token"]
    H = _bearer(tok)
    client.patch("/profile", json={"weight_kg": 80}, headers=H)
    client.post("/benchmarks/record", json={
        "benchmark_id": "bench_1rm", "result_value": 120, "result_unit": "kg",
        "test_date": "2026-06-20"}, headers=H)
    prof = client.get("/profile", headers=H).json()
    assert prof["current"]["bench_ratio"] == 120   # = 1RM ; le rapport /poids derrière


def test_program_restart_resets_progression(client, monkeypatch):
    monkeypatch.setenv("INVITE_CODE", "1995")
    tok = client.post("/auth/register", json={
        "email": "restart@b.com", "password": "password1", "invite_code": "1995"}).json()["token"]
    H = _bearer(tok)
    # redémarre le programme : J0 = lundi 2027-03-01 (grande semaine)
    client.patch("/profile", json={"work_schedule": {
        "type": "police_3223", "anchor_big_week_monday": "2027-03-01"}}, headers=H)
    j0 = client.get("/plan/day?date=2027-03-01", headers=H).json()      # lundi J0
    assert j0["week_index"] == 0 and j0["week_type"] == "big_work"       # cycle 0, grande
    plus2 = client.get("/plan/day?date=2027-03-15", headers=H).json()    # +2 semaines
    assert plus2["week_index"] == 2
