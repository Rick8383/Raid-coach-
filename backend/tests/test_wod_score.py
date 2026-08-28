"""Saisie / correction du score d'un WOD + commentaire honnête de performance."""
import pytest
from fastapi.testclient import TestClient

from engines.wod_generator import assess, score_label


@pytest.fixture()
def client() -> TestClient:
    import importlib
    from api import main as api_main
    importlib.reload(api_main)
    return TestClient(api_main.app)


def _save_wod(client, date: str, name: str, result: dict, fmt: str = "rft"):
    return client.post("/sessions/save", json={
        "discipline": "crossfit", "session_date": date, "duration_min": 20,
        "intensity_rpe": 9, "status": "done", "title": name,
        "detail": {"name": name, "format_key": fmt, "description": ["x"],
                   "result": result}}).json()


# ---------- Commentaire honnête (moteur pur) ----------
def test_capped_wod_is_called_out():
    a = assess({"mode": "for_time", "time_sec": 900, "capped": True, "cap_sec": 900}, [])
    assert a["verdict"] == "non terminé"
    assert "pas fini" in a["comment"]


def test_first_attempt_is_a_reference_not_praise():
    a = assess({"mode": "for_time", "time_sec": 700, "capped": False,
                "cap_sec": 900, "format_key": "rft"}, [])
    assert a["verdict"] == "référence posée"
    assert a["reference"] is None


def test_regression_is_stated_plainly():
    hist = [{"mode": "for_time", "time_sec": 600, "capped": False, "format_key": "rft"}]
    a = assess({"mode": "for_time", "time_sec": 720, "capped": False,
                "cap_sec": 900, "format_key": "rft"}, hist)
    assert a["verdict"] == "en retrait"
    assert a["delta_pct"] == 20.0
    assert "plus lent" in a["comment"]


def test_record_is_recognised():
    hist = [{"mode": "for_time", "time_sec": 720, "capped": False, "format_key": "rft"}]
    a = assess({"mode": "for_time", "time_sec": 660, "capped": False,
                "cap_sec": 900, "format_key": "rft"}, hist)
    assert a["verdict"] == "record" and a["delta_pct"] < 0


def test_amrap_compares_reps():
    hist = [{"mode": "amrap", "reps": 150, "format_key": "amrap"}]
    worse = assess({"mode": "amrap", "reps": 120, "format_key": "amrap"}, hist)
    better = assess({"mode": "amrap", "reps": 165, "format_key": "amrap"}, hist)
    assert worse["verdict"] == "en retrait" and better["verdict"] == "record"


def test_score_label_formats():
    assert score_label({"mode": "for_time", "time_sec": 754}) == "12:34"
    assert score_label({"mode": "for_time", "time_sec": 900, "capped": True}) == "15:00 (cap)"
    # Score AMRAP : « tours + reps du tour en cours » (cf. test dédié plus bas).
    assert score_label({"mode": "amrap", "rounds": 2, "reps": 22}) == "2 tours + 22 reps"


# ---------- Édition depuis l'agenda ----------
def test_score_can_be_entered_and_corrected_from_agenda(client):
    saved = _save_wod(client, "2028-05-01", "OPÉRATION TEST",
                      {"mode": "for_time", "time_sec": 800, "capped": False, "cap_sec": 900})
    sid = saved["session_id"]

    r = client.patch(f"/sessions/{sid}/score", json={
        "mode": "for_time", "time_sec": 754, "capped": False, "cap_sec": 900}).json()
    assert r["score_label"] == "12:34"
    assert r["assessment"]["verdict"] in ("record", "stable", "en retrait", "référence posée")

    # La correction MET À JOUR la séance, elle n'en crée pas une seconde.
    rows = [s for s in client.get("/sessions/recent?n=80").json()["sessions"]
            if s["session_date"] == "2028-05-01"]
    assert len(rows) == 1
    week = client.post("/agenda/week", json={"date": "2028-05-01"}).json()
    day = next(d for d in week["days"] if d["date"] == "2028-05-01")
    entry = next(e for e in day["done_all"] if e["id"] == sid)
    assert entry["score_label"] == "12:34"
    assert entry["wod_result"]["time_sec"] == 754
    assert entry["assessment"]["comment"]


def test_score_edit_records_rounds_and_distance(client):
    saved = _save_wod(client, "2028-05-08", "AMRAP TEST",
                      {"mode": "amrap", "reps": 100}, fmt="amrap")
    sid = saved["session_id"]
    r = client.patch(f"/sessions/{sid}/score", json={
        "mode": "amrap", "reps": 138, "rounds": 9, "distance_m": 1200,
        "time_sec": 720, "cap_sec": 720, "notes": "scaling 20 kg"}).json()
    assert r["score_label"] == "9 tours + 138 reps"
    week = client.post("/agenda/week", json={"date": "2028-05-08"}).json()
    day = next(d for d in week["days"] if d["date"] == "2028-05-08")
    res = next(e for e in day["done_all"] if e["id"] == sid)["wod_result"]
    assert res["rounds"] == 9 and res["distance_m"] == 1200


def test_score_edit_rejects_non_crossfit_and_unknown(client):
    run = client.post("/sessions/save", json={
        "discipline": "run", "session_date": "2028-05-15", "duration_min": 45,
        "intensity_rpe": 7, "status": "done", "title": "Z2"}).json()
    assert client.patch(f"/sessions/{run['session_id']}/score",
                        json={"mode": "amrap", "reps": 10}).status_code == 409
    assert client.patch("/sessions/999999/score",
                        json={"mode": "amrap", "reps": 10}).status_code == 404


def test_timer_save_returns_assessment(client):
    """Le chrono enregistre → le serveur renvoie directement le verdict."""
    res = _save_wod(client, "2028-05-22", "CHRONO TEST",
                    {"mode": "amrap", "reps": 120}, fmt="amrap")
    assert res["assessment"]["comment"]
    assert res["assessment"]["verdict"]


def test_score_on_a_planned_wod_marks_it_done(client):
    """Cas réel : le WOD du jour est encore « prévu » dans l'agenda. Saisir son
    score doit le faire passer à FAIT et compter sa charge — sans quoi aucun
    bouton de score n'était accessible sur la séance."""
    saved = client.post("/sessions/save", json={
        "discipline": "crossfit", "session_date": "2028-06-05", "duration_min": 20,
        "status": "planned", "title": "PROTOCOLE OBSIDIENNE",
        "detail": {"name": "PROTOCOLE OBSIDIENNE", "format_key": "amrap",
                   "description": ["x"]}}).json()
    sid = saved["session_id"]

    week = client.post("/agenda/week", json={"date": "2028-06-05"}).json()
    day = next(d for d in week["days"] if d["date"] == "2028-06-05")
    entry = next(e for e in day["done_all"] if e["id"] == sid)
    assert entry["status"] == "planned"
    assert entry["wod_format_key"] == "amrap"      # → pré-remplit le type de score

    r = client.patch(f"/sessions/{sid}/score", json={
        "mode": "amrap", "reps": 146, "rounds": 9, "time_sec": 720}).json()
    assert r["persisted_status"] == "done"
    assert r["score_label"] == "9 tours + 146 reps"

    rows = [s for s in client.get("/sessions/recent?n=80").json()["sessions"]
            if s["session_date"] == "2028-06-05"]
    assert len(rows) == 1                          # mise à jour, pas de doublon
    assert rows[0]["status"] == "done"
    assert float(rows[0]["stress_units"]) > 0      # la charge est enfin comptée


# ---------- Score AMRAP : tours complets + reps du tour EN COURS ----------
def test_rounds_and_partial_reps_are_distinct():
    """Cas réel : 2 tours finis puis 22 reps avant de bloquer sur les burpees.
    Avant, « 22 » seul était ambigu (22 reps ? 22 tours ? 1000 m = 1000 reps ?)."""
    assert score_label({"mode": "amrap", "rounds": 2, "reps": 22}) == "2 tours + 22 reps"
    assert score_label({"mode": "amrap", "rounds": 1, "reps": 0}) == "1 tour"
    assert score_label({"mode": "amrap", "rounds": 3, "reps": 0}) == "3 tours"
    assert score_label({"mode": "amrap", "rounds": 0, "reps": 0}) == "score non saisi"
    # Rétro-compatibilité : anciens scores sans tours.
    assert score_label({"mode": "amrap", "rounds": 0, "reps": 142}) == "142 reps"


def test_rounds_outrank_partial_reps():
    """Classement de compétition : les tours d'abord, les reps départagent."""
    hist = [{"mode": "amrap", "rounds": 2, "reps": 22, "format_key": "amrap"}]
    assert assess({"mode": "amrap", "rounds": 3, "reps": 0,
                   "format_key": "amrap"}, hist)["verdict"] == "record"
    assert assess({"mode": "amrap", "rounds": 2, "reps": 30,
                   "format_key": "amrap"}, hist)["verdict"] == "record"
    assert assess({"mode": "amrap", "rounds": 2, "reps": 22,
                   "format_key": "amrap"}, hist)["verdict"] == "stable"
    # 1 tour + 40 reps reste DERRIÈRE 2 tours + 22 reps, malgré plus de reps.
    assert assess({"mode": "amrap", "rounds": 1, "reps": 40,
                   "format_key": "amrap"}, hist)["verdict"] == "en retrait"


def test_partial_reps_percentage_only_when_comparable():
    """Un % n'a de sens qu'à nombre de tours égal — sinon il mélangerait
    tours et reps."""
    hist = [{"mode": "amrap", "rounds": 2, "reps": 22, "format_key": "amrap"}]
    same = assess({"mode": "amrap", "rounds": 2, "reps": 30, "format_key": "amrap"}, hist)
    other = assess({"mode": "amrap", "rounds": 3, "reps": 5, "format_key": "amrap"}, hist)
    assert same["delta_pct"] is not None
    assert other["delta_pct"] is None


def test_rounds_reps_round_trip_through_the_api(client):
    saved = client.post("/sessions/save", json={
        "discipline": "crossfit", "session_date": "2028-06-12", "duration_min": 20,
        "status": "planned", "title": "WOD TOURS",
        "detail": {"name": "WOD TOURS", "format_key": "amrap", "description": ["x"]}}).json()
    r = client.patch(f"/sessions/{saved['session_id']}/score", json={
        "mode": "amrap", "rounds": 2, "reps": 22, "time_sec": 720}).json()
    assert r["score_label"] == "2 tours + 22 reps"
    week = client.post("/agenda/week", json={"date": "2028-06-12"}).json()
    day = next(d for d in week["days"] if d["date"] == "2028-06-12")
    e = next(x for x in day["done_all"] if x["id"] == saved["session_id"])
    assert e["wod_result"]["rounds"] == 2 and e["wod_result"]["reps"] == 22
