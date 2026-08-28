"""RAID Coach API — FastAPI application.
Run: uvicorn api.main:app --reload
Docs auto-générées: http://localhost:8000/docs
"""
from __future__ import annotations

import json
import os
import re
from contextvars import ContextVar
from datetime import date as _date

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from api import garmin
from api.garmin import GarminTokenStore
from api.persistence import Store
from api.services.coach_api import CoachAPI
from api import auth as _auth
from engines.coach_chat import answer as _coach_chat_answer
from engines.coach_chat import llm_answer as _coach_llm, llm_enabled as _coach_llm_enabled
from engines import standby as _standby
from engines.mobility import generate_mobility as _gen_mobility
from engines.wod_generator import scoring as _wod_scoring
from engines.schedule import user_schedule as _us
# CoachAPI met engines/legacy sur sys.path à l'import → AnalyticsInput accessible
from build6_analytics_engine.models import AnalyticsInput  # noqa: E402

app = FastAPI(
    title="RAID Coach Elite+ API",
    version="1.0.0",
    description="Backend API exposant tous les moteurs RAID Coach (B3-B11)",
)

# CORS : l'app web/mobile appelle l'API depuis une autre origine.
# CORS_ORIGINS (CSV) en prod ; "*" par défaut pour la beta perso.
_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

coach = CoachAPI()
store = Store()
garmin_tokens = GarminTokenStore(store.db)

# Visible dans les logs Render → confirme la persistance d'un coup d'œil.
print("[raid-coach] DB backend: "
      + ("postgres (persistant)" if store.db.is_postgres else "sqlite (EPHEMERE — voir DEPLOY.md)"),
      flush=True)

# ---------- Authentification multi-utilisateurs (par athlète) ----------
# Secret de signature des jetons (stable, stocké en base → survit aux redéploys).
_AUTH_SECRET = store.auth_secret()
# user_id de la requête courante, posé par le middleware (None si anonyme).
_current_uid: ContextVar[int | None] = ContextVar("current_uid", default=None)


class _AuthMiddleware:
    """Middleware ASGI pur (contextvar fiable jusqu'au handler, même sync) :
    lit le jeton Bearer, en déduit l'user_id, le pose dans le contexte."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            uid = None
            for k, v in scope.get("headers", []):
                if k == b"authorization":
                    tok = _auth.bearer(v.decode("latin-1"))
                    if tok:
                        uid = _auth.verify_token(tok, _AUTH_SECRET)
                    break
            _current_uid.set(uid)
        await self.app(scope, receive, send)


app.add_middleware(_AuthMiddleware)


def _owner_athlete() -> int:
    return store.__dict__["athlete_id"]  # athlète primaire = propriétaire


def _aid() -> int:
    """athlete_id de l'utilisateur connecté. Repli sur le propriétaire si aucun
    jeton (compat mono-utilisateur), sauf si AUTH_REQUIRED est défini → 401."""
    uid = _current_uid.get()
    if uid is not None:
        aid = store.athletes.athlete_id_for_user(uid)
        if aid is not None:
            return aid
    if os.environ.get("AUTH_REQUIRED"):
        raise HTTPException(status_code=401, detail="Authentification requise")
    return _owner_athlete()


def _require_uid() -> int:
    uid = _current_uid.get()
    if uid is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return uid


def _schedule_config() -> dict:
    """Rythme de travail de l'athlète courant (3/2/2/3 ou hebdo), normalisé."""
    prof = store.athletes.get_profile(_aid()) or {}
    ws = prof.get("work_schedule")
    if isinstance(ws, str) and ws:
        try:
            ws = json.loads(ws)
        except (ValueError, TypeError):
            ws = None
    return _us.normalize(ws if isinstance(ws, dict) else None)


# 1RM par mouvement (benchmark `{lift}_1rm`) → charges 5/3/1 personnalisées.
_STRENGTH_LIFTS = ("bench", "squat", "ohp", "row")

# Nom affiché du mouvement principal → clé de benchmark 1RM (autorégulation :
# la série AMRAP loggée sert à proposer une mise à jour du 1RM — Helms 2016).
_LIFT_NAME_TO_KEY = {
    "développé couché": "bench", "bench": "bench",
    "squat": "squat",
    "presse militaire": "ohp", "développé militaire": "ohp", "ohp": "ohp",
    "rowing": "row", "row": "row",
}


def _lift_key_of(name: str) -> str | None:
    low = (name or "").strip().lower()
    for frag, key in _LIFT_NAME_TO_KEY.items():
        if frag in low:
            return key
    return None


def _performed_entries(perf: dict | None) -> list[dict]:
    """Séries enregistrées, quel que soit le format : `{lift, sets, est_1rm}`
    (séance à un mouvement principal) ou `{lifts: [...]}` (séance combinée
    haut du corps : développé + rowing dans la même séance)."""
    if not isinstance(perf, dict):
        return []
    if isinstance(perf.get("lifts"), list):
        return [e for e in perf["lifts"] if isinstance(e, dict)]
    return [perf] if perf.get("lift") else []


def _logged_e1rm(aid: int) -> dict[str, float]:
    """Meilleur 1RM estimé (Epley) déduit des SÉRIES RÉELLEMENT ENREGISTRÉES.

    Les charges du plan doivent suivre ce que l'athlète soulève vraiment : sans
    ça, logger « rowing 6×90 kg » ne changeait rien tant qu'on n'avait pas tapé
    manuellement sur la suggestion de 1RM, et la séance suivante repartait sur
    des charges périmées."""
    best: dict[str, float] = {}
    for s in store.sessions.last_n(aid, 60):
        if s["status"] != "done":
            continue
        for entry in _performed_entries((_detail_of(s) or {}).get("performed")):
            key = _lift_key_of(str(entry.get("lift") or ""))
            sets = entry.get("sets")
            if not key or not isinstance(sets, list):
                continue
            for st in sets:
                if not isinstance(st, dict):
                    continue
                try:
                    reps, load = int(st.get("reps") or 0), float(st.get("load_kg") or 0)
                except (TypeError, ValueError):
                    continue
                # Epley reste fiable jusqu'à ~12 reps ; au-delà l'estimation dérive.
                if 1 <= reps <= 12 and load > 0:
                    best[key] = max(best.get(key, 0.0), load * (1 + reps / 30))
    return best


def _strength_maxes() -> dict:
    """1RM (kg) de l'athlète courant par mouvement : le meilleur entre son
    benchmark `{lift}_1rm` et ce que ses séries enregistrées démontrent.
    Mouvement absent partout → défaut du moteur."""
    aid = _aid()
    logged = _logged_e1rm(aid)
    out: dict[str, float] = {}
    for lift in _STRENGTH_LIFTS:
        prog = store.benchmarks.progression(aid, f"{lift}_1rm")
        recorded = float(prog[-1]["result_value"]) if prog else 0.0
        value = max(recorded, logged.get(lift, 0.0))
        if value > 0:
            out[lift] = round(value * 2) / 2   # arrondi 0,5 kg
    return out


def _safe(fn, payload: dict) -> dict:
    try:
        return fn(payload)
    except (ValueError, KeyError, TypeError) as e:
        # TypeError inclus : les champs dict/list[dict] non typés (sessions,
        # goals, current) peuvent contenir de mauvais types → 422, pas 500
        raise HTTPException(status_code=422, detail=str(e))


# ---------- Schemas (request validation) ----------
class DailyDecisionIn(BaseModel):
    day_of_week: str = Field(pattern="^(mon|tue|wed|thu|fri|sat|sun)$")
    is_work_day: bool
    week_type: str = Field(pattern="^(big_work|small_work)$")
    readiness: float = Field(ge=0, le=100)
    fatigue: float = Field(ge=0, le=100)
    sleep_quality: float = Field(ge=0, le=100)
    pain_flag: bool = False
    sciatic_flare: bool = False
    budget_consumed_pct: float = Field(default=0, ge=0, le=200)
    days_since_rest: int = Field(default=0, ge=0)
    last_two_disciplines: list[str] = []
    weeks_to_main_goal: int | None = None


class SessionTodayIn(BaseModel):
    # check-in du jour
    readiness: float = Field(ge=0, le=100)
    fatigue: float = Field(ge=0, le=100)
    sleep_quality: float = Field(ge=0, le=100)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sciatic_flare: bool = False
    pain_flag: bool = False
    # contexte planning : si `date` est fourni, jour/semaine sont calés sur le 3/2/2/3
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    day_of_week: str | None = Field(default=None, pattern="^(mon|tue|wed|thu|fri|sat|sun)$")
    is_work_day: bool | None = None
    week_type: str | None = Field(default=None, pattern="^(big_work|small_work)$")
    weeks_to_main_goal: int | None = None
    # défauts None → calculés depuis l'historique si non fournis (boucle adaptative)
    last_two_disciplines: list[str] | None = None
    budget_consumed_pct: float | None = Field(default=None, ge=0, le=200)
    days_since_rest: int | None = Field(default=None, ge=0)
    terrain: str = "trail"
    athlete_level: str = "intermediate"


class ScheduleIn(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class RoadmapIn(BaseModel):
    weeks_to_selection: int = Field(ge=8, le=220)
    current_week: int = Field(default=0, ge=0, le=220)


class WeeklyBudgetIn(BaseModel):
    week_type: str
    sessions: list[dict] = []


class GoalsIn(BaseModel):
    goals: list[dict]


class HRProfileIn(BaseModel):
    age: int = Field(ge=14, le=80)
    fc_max: int | None = None
    fc_rest: int | None = None


class PredictionIn(BaseModel):
    distance_km: float = Field(ge=1, le=100)
    time_sec: int = Field(ge=180, le=60000)


class PaceTableIn(BaseModel):
    vma_kmh: float = Field(ge=8, le=26)
    terrain: str = "road"
    elevation_gain_m_per_km: float = Field(default=0, ge=0, le=200)
    load_kg: float = Field(default=0, ge=0, le=40)


class StrengthSessionIn(BaseModel):
    recovery_score: float = Field(ge=0, le=100)
    sleep_quality: float = Field(ge=0, le=100)
    pain_flag: bool = False
    hrv_trend: str = "stable"
    run_load_7d: float = Field(default=0, ge=0, le=100)
    crossfit_load_7d: float = Field(default=0, ge=0, le=100)
    strength_load_7d: float = Field(default=0, ge=0, le=100)
    sessions_since_deload: int = Field(default=0, ge=0)
    week_in_block: int = 0
    weeks_to_goal: int | None = None
    athlete_level: str = "intermediate"
    raid_focus: bool = True
    recent_family_ids: list[str] = []
    seed: str = ""


class PRIn(BaseModel):
    movement_id: str
    weight_kg: float = Field(ge=0)
    reps: int = Field(ge=1, le=50)
    date: str = "2026-01-01"


class RaidStrengthIn(BaseModel):
    current: dict
    bodyweight_kg: float = Field(ge=40, le=180)
    tier: str = Field(default="pass", pattern="^(pass|elite)$")


class AutoPlanIn(BaseModel):
    goal_type: str
    goal_name: str
    duration_weeks: int = Field(ge=4, le=52)
    analytics: dict


class MacrosIn(BaseModel):
    weight_kg: float = Field(ge=40, le=180)
    height_cm: float = Field(ge=140, le=220)
    age: int = Field(ge=14, le=80)
    sex: str = "m"
    body_fat_pct: float | None = None
    target_weight_kg: float | None = None
    phase: str = "recomp"
    activity: str = "moderate"
    # Si fournie, l'activité est AUTO-DÉRIVÉE des séances planifiées ce jour-là
    # (périodisation glucidique « fuel for the work required » — Impey 2018).
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class WeightIn(BaseModel):
    weight_kg: float = Field(ge=40, le=180)


class MetricsRecordIn(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    readiness: float | None = Field(default=None, ge=0, le=100)
    fatigue: float | None = Field(default=None, ge=0, le=100)
    sleep_quality: float | None = Field(default=None, ge=0, le=100)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    hrv: float | None = Field(default=None, ge=0, le=300)        # HRV SDNN (ms), wearable
    resting_hr: int | None = Field(default=None, ge=25, le=120)  # FC repos (bpm), wearable
    weight_kg: float | None = Field(default=None, ge=40, le=180)
    pain_flag: bool = False
    sciatic_flare: bool = False
    notes: str | None = None


class SessionCompleteIn(BaseModel):
    discipline: str = Field(pattern="^(run|crossfit|strength|swim|recovery)$")
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_min: int = Field(ge=0, le=600)
    intensity_rpe: float = Field(ge=0, le=10)
    stress_units: float = Field(default=0, ge=0)
    family_id: str | None = None
    template_id: str | None = None
    detail: dict = {}
    feedback: dict = {}


class BenchmarkRecordIn(BaseModel):
    benchmark_id: str
    result_value: float
    result_unit: str
    test_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    detail: dict = {}


class SessionSaveIn(BaseModel):
    """Enregistre une séance générée dans l'historique/agenda (planifiée ou faite)."""
    discipline: str = Field(pattern="^(run|strength|crossfit|swim|recovery)$")
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_min: int = Field(ge=0, le=300)
    intensity_rpe: float = Field(default=7.0, ge=1, le=10)
    title: str | None = None
    status: str = Field(default="planned", pattern="^(planned|done)$")
    detail: dict = {}
    # Données réelles de la montre (Garmin) saisies à la main — toutes optionnelles,
    # rangées dans detail["metrics"], isolées au profil courant (athlete_id).
    distance_km: float | None = Field(default=None, ge=0, le=1000)
    hr_avg: int | None = Field(default=None, ge=30, le=230)
    hr_max: int | None = Field(default=None, ge=30, le=230)
    elevation_m: int | None = Field(default=None, ge=0, le=12000)
    calories: int | None = Field(default=None, ge=0, le=20000)
    avg_pace: str | None = Field(default=None, max_length=12)
    te_aerobic: float | None = Field(default=None, ge=0, le=5)
    te_anaerobic: float | None = Field(default=None, ge=0, le=5)
    cadence_spm: int | None = Field(default=None, ge=0, le=260)
    # Séries de force réellement réalisées (reps × charge par série) + 1RM estimé.
    # {"lift": str, "sets": [{"reps": int, "load_kg": float, "top": bool}], "est_1rm": float}
    performed: dict | None = None


class ManualSessionIn(BaseModel):
    """Séance LIBRE (hors plan) saisie à la main : vélo, boxe, JJB, natation…
    → enregistrée comme faite et prise en compte dans le suivi (charge/ACWR)."""
    activity: str = Field(min_length=1, max_length=80)   # libellé affiché
    discipline: str = Field(default="other",
                            pattern="^(run|strength|crossfit|swim|recovery|cycling|combat|hiking|mobility|other)$")
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_min: int = Field(ge=1, le=600)
    intensity_rpe: float = Field(default=6.0, ge=1, le=10)
    distance_km: float | None = Field(default=None, ge=0, le=1000)
    hr_avg: int | None = Field(default=None, ge=30, le=230)
    hr_max: int | None = Field(default=None, ge=30, le=230)
    elevation_m: int | None = Field(default=None, ge=0, le=12000)
    calories: int | None = Field(default=None, ge=0, le=20000)
    notes: str | None = Field(default=None, max_length=500)



class ProfileUpdateIn(BaseModel):
    weight_kg: float | None = Field(default=None, ge=40, le=180)
    target_weight_kg: float | None = Field(default=None, ge=40, le=180)
    body_fat_pct: float | None = Field(default=None, ge=3, le=50)
    height_cm: float | None = Field(default=None, ge=140, le=220)
    fc_max: int | None = Field(default=None, ge=120, le=230)
    fc_rest: int | None = Field(default=None, ge=30, le=120)
    vma_kmh: float | None = Field(default=None, ge=8, le=26)
    main_goal: str | None = None
    goal_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    # rythme de travail : {"type":"police_3223","anchor_big_week_monday":"YYYY-MM-DD"}
    # ou {"type":"weekly","training_days":["mon","wed",...]} (validé/normalisé serveur)
    work_schedule: dict | None = None


class RegisterIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=200)
    password: str = Field(min_length=8, max_length=200)
    invite_code: str | None = Field(default=None, max_length=200)
    name: str | None = Field(default=None, max_length=80)


class LoginIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=200)
    password: str = Field(min_length=1, max_length=200)


class InviteCodeIn(BaseModel):
    invite_code: str = Field(default="", max_length=80)


class StandbyIn(BaseModel):
    """Active le mode standby/vacances sur une fenêtre de dates (par athlète)."""
    mode: str = Field(pattern="^(pause|vacation)$")
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    sessions_per_day: int = Field(default=1, ge=1, le=2)  # mode vacances
    equipment: str = Field(default="gym", pattern="^(gym|minimal|bodyweight)$")


class GenerateIn(BaseModel):
    discipline: str = Field(pattern="^(run|strength|crossfit)$")
    duration_min: int | None = Field(default=None, ge=10, le=180)
    intensity_cap: float | None = Field(default=None, ge=1, le=10)
    terrain: str = "trail"
    athlete_level: str = "intermediate"
    weeks_to_main_goal: int | None = None
    wod_kind: str = Field(default="death_by", pattern="^(death_by|time_cap)$")
    seed: str | None = None  # change à chaque clic → séance différente


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    history: list[dict] = Field(default_factory=list)  # tours précédents (role/content)


def _chat_context(for_date: str | None) -> dict:
    """Assemble le contexte du coach (profil, métriques du jour, planning) depuis
    le store pour personnaliser la réponse du chat."""
    ctx: dict = {"profile": store.profile_payload(_aid())}
    latest = store.metrics.latest(_aid())
    if latest:
        ctx["metrics"] = latest
    try:
        day = for_date or _date.today().isoformat()
        ctx["today"] = coach.schedule_day({"date": day}, _schedule_config())
    except (ValueError, KeyError):
        pass
    goal_date = (ctx["profile"] or {}).get("goal_date")
    if goal_date:
        try:
            delta = (_date.fromisoformat(goal_date) - _date.today()).days
            ctx["weeks_to_goal"] = max(0, delta // 7)
        except ValueError:
            pass
    return ctx


def _detail_of(session: dict) -> dict:
    """Parse le detail_json d'une séance (stocké en chaîne) → dict (vide si KO)."""
    raw = session.get("detail_json")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        try:
            d = json.loads(raw)
            return d if isinstance(d, dict) else {}
        except (ValueError, TypeError):
            return {}
    return {}


def _wod_score(detail: dict) -> dict | None:
    """Extrait le score d'un WOD chronométré depuis le détail de séance.
    Renvoie {type, value, label, capped, cap_sec} ou None."""
    res = detail.get("result")
    if not isinstance(res, dict) or res.get("mode") not in ("for_time", "amrap"):
        return None
    mode = res["mode"]
    is_time = mode == "for_time"
    value = res.get("time_sec") if is_time else res.get("reps")
    return {
        "type": "time" if is_time else "reps",
        "value": value,
        "label": detail.get("score_label"),
        "capped": bool(res.get("capped")),
        "cap_sec": res.get("cap_sec"),
    }


def _wod_performance(res: dict, best_reps: float | None) -> float | None:
    """Score de performance 0-100 d'un WOD chronométré, pour l'analyse.
    - For Time : plus on finit sous le time cap, mieux c'est (capé → 45).
    - AMRAP : reps relatives au meilleur score AMRAP connu de l'athlète."""
    mode = res.get("mode")
    if mode == "for_time":
        cap = float(res.get("cap_sec") or 0)
        t = float(res.get("time_sec") or 0)
        if res.get("capped") or cap <= 0 or t <= 0:
            return 45.0
        return max(0.0, min(100.0, 60.0 + 40.0 * (cap - t) / cap))
    if mode == "amrap":
        reps = float(res.get("reps") or 0)
        if not best_reps or best_reps <= 0:
            return 65.0  # premier score AMRAP : référence neutre
        return max(0.0, min(100.0, 40.0 + 60.0 * reps / best_reps))
    return None


def _analytics_from_store() -> dict:
    """Dérive un instantané analytics des séances et métriques enregistrées.
    Renvoie un statut 'warming_up' tant que l'historique est trop court."""
    sessions = store.sessions.last_n(_aid(), 28)
    loads = [float(s["stress_units"] or 0) for s in sessions if s["status"] == "done"]
    metrics = store.db.query(
        """SELECT readiness, fatigue, sleep_quality FROM daily_metrics
           WHERE athlete_id = ? ORDER BY metric_date DESC LIMIT 14""",
        (_aid(),))
    readiness = [float(m["readiness"]) for m in metrics if m["readiness"] is not None]
    recovery = [100.0 - float(m["fatigue"]) for m in metrics if m["fatigue"] is not None]

    if len(loads) < 3 or len(readiness) < 3:
        return {"status": "warming_up",
                "message": "Pas encore assez de données — enregistre quelques séances et check-ins.",
                "sessions_logged": len(loads), "metrics_logged": len(readiness)}

    # Performance réelle = score des WOD chronométrés (For Time vs time cap,
    # AMRAP vs meilleur score connu). Parcouru du plus ancien au plus récent
    # pour une tendance cohérente. Repli sur la readiness si < 3 WOD scorés.
    wod_perf: list[float] = []
    best_amrap = 0.0
    for s in reversed(sessions):
        if s["status"] != "done":
            continue
        res = _detail_of(s).get("result")
        if isinstance(res, dict) and res.get("mode") in ("for_time", "amrap"):
            p = _wod_performance(res, best_amrap or None)
            if p is not None:
                wod_perf.append(p)
            if res.get("mode") == "amrap":
                best_amrap = max(best_amrap, float(res.get("reps") or 0))
    performance_scores = wod_perf if len(wod_perf) >= 3 else readiness

    # Distribution d'intensité course 80/20 (Seiler 2006 ; Stöggl & Sperlich
    # 2014) : ~80 % du volume course en basse intensité (RPE ≤ 4). Pondéré par
    # la durée, sur les 28 dernières séances enregistrées.
    run_low = run_high = 0
    for s in sessions:
        if s["status"] == "done" and s["discipline"] == "run":
            dur = int(s["duration_min"] or 0)
            if float(s["intensity_rpe"] or 7) <= 4.5:
                run_low += dur
            else:
                run_high += dur
    run_total = run_low + run_high
    intensity = None
    if run_total >= 60:   # au moins ~1h de course loggée pour être parlant
        low_pct = round(100 * run_low / run_total)
        intensity = {
            "low_pct": low_pct, "target_low_pct": 80,
            "low_min": run_low, "high_min": run_high,
            "message": ("Bonne base : garde tes footings VRAIMENT faciles."
                        if low_pct >= 75 else
                        "Trop d'intensité : tes séances faciles doivent rester faciles (RPE ≤ 4)."),
        }

    chronic = sum(loads) / len(loads)
    data = AnalyticsInput(
        recent_loads=loads[:7], chronic_load=chronic,
        readiness_scores=readiness, recovery_scores=recovery,
        performance_scores=performance_scores,
        weakness_scores={})
    r = coach.analytics.analyze(data)
    return {
        "intensity_distribution": intensity,
        "status": r.global_status,
        "fitness": round(r.fitness.score, 1),
        "fatigue": round(r.fatigue.score, 1),
        "acwr": round(r.fatigue.acute_chronic_ratio, 2),
        "readiness": round(r.readiness.score, 1),
        "readiness_trend": r.readiness.trend.value,
        "performance": round(r.performance.score, 1),
        "performance_source": "wod" if len(wod_perf) >= 3 else "readiness_proxy",
        "wods_scored": len(wod_perf),
        "risk": r.risk.level.value,
        "risk_reasons": r.risk.reasons,
        "sessions_logged": len(loads),
    }


# ---------- Routes ----------
@app.get("/health")
def health() -> dict:
    # `persistent` = true seulement sur PostgreSQL (données conservées entre
    # redéploiements). En SQLite sur Render free, la base est éphémère → false.
    persistent = bool(getattr(store.db, "is_postgres", False))
    return {"status": "ok", "service": "raid-coach-api", "version": "1.0.0",
            "db_backend": "postgres" if persistent else "sqlite",
            "persistent": persistent}


# ---------- Authentification (inscription par code d'invitation, 1er = proprio) ----------
def _user_public(uid: int, email: str) -> dict:
    return {"id": uid, "email": email, "is_owner": store.owner_user_id() == uid}


@app.post("/auth/register")
def auth_register(body: RegisterIn) -> dict:
    email = body.email.strip().lower()
    if store.athletes.find_user_by_email(email):
        raise HTTPException(status_code=409, detail="Cet email a déjà un compte.")
    if store.owner_user_id() is None:
        # 1er inscrit = propriétaire → récupère le profil existant (données intactes)
        uid, _ = store.claim_owner(email, _auth.hash_password(body.password))
    else:
        # Code d'invitation : géré dans l'app par le propriétaire (app_meta),
        # avec repli sur la variable d'env INVITE_CODE.
        code = store.meta.get("invite_code") or os.environ.get("INVITE_CODE")
        if not code:
            raise HTTPException(status_code=403,
                                detail="Inscriptions fermées (aucun code d'invitation défini).")
        if (body.invite_code or "").strip() != code:
            raise HTTPException(status_code=403, detail="Code d'invitation invalide.")
        uid, _ = store.register_user(email, _auth.hash_password(body.password), body.name or "Athlète")
    return {"token": _auth.make_token(uid, _AUTH_SECRET), "user": _user_public(uid, email)}


@app.post("/auth/login")
def auth_login(body: LoginIn) -> dict:
    email = body.email.strip().lower()
    user = store.athletes.find_user_by_email(email)
    if not user or not _auth.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return {"token": _auth.make_token(user["id"], _AUTH_SECRET),
            "user": _user_public(user["id"], user["email"])}


def _invite_code() -> str | None:
    return store.meta.get("invite_code") or os.environ.get("INVITE_CODE")


@app.get("/auth/me")
def auth_me() -> dict:
    uid = _require_uid()
    user = store.athletes.get_user(uid)
    if not user:
        raise HTTPException(status_code=401, detail="Session expirée.")
    return {"user": _user_public(uid, user["email"]),
            "registration_open": store.owner_user_id() is None or bool(_invite_code())}


def _require_owner() -> int:
    uid = _require_uid()
    if store.owner_user_id() != uid:
        raise HTTPException(status_code=403, detail="Réservé au propriétaire.")
    return uid


@app.get("/auth/invite-code")
def get_invite_code() -> dict:
    """Code d'invitation courant (propriétaire uniquement) — à donner aux amis."""
    _require_owner()
    return {"invite_code": store.meta.get("invite_code") or "",
            "env_fallback": bool(os.environ.get("INVITE_CODE"))}


@app.post("/auth/invite-code")
def set_invite_code(body: InviteCodeIn) -> dict:
    """Définit/efface le code d'invitation (propriétaire) — stocké en base, privé."""
    _require_owner()
    store.meta.set("invite_code", body.invite_code.strip())
    return {"invite_code": store.meta.get("invite_code") or ""}


@app.post("/coach/daily-decision")
def daily_decision(body: DailyDecisionIn) -> dict:
    return _safe(coach.daily_decision, body.model_dump())


def _adaptive_context(payload: dict) -> dict:
    """Calcule depuis l'historique stocké les entrées que le coach exploite :
    disciplines récentes, budget fatigue hebdo consommé, jours d'entraînement
    consécutifs, ACWR. Requiert une `date` (sinon contexte vide)."""
    from datetime import date, timedelta
    if not payload.get("date"):
        return {}
    day = date.fromisoformat(payload["date"])
    week_type = coach.schedule_day({"date": payload["date"]}, _schedule_config())["week_type"]
    monday = (day - timedelta(days=day.weekday())).isoformat()
    yesterday = (day - timedelta(days=1)).isoformat()

    done = [s for s in store.sessions.last_n(_aid(), 40) if s["status"] == "done"]
    last_two = [s["discipline"] for s in done[:2]]

    consumed = store.sessions.stress_units_between(_aid(), monday, payload["date"])
    # le budget hebdo n'existe que pour le 3/2/2/3 ; sinon (hebdo) → base modérée
    budget = coach.weekly_budget_su(week_type if week_type in ("big_work", "small_work") else "small_work")
    budget_pct = round(consumed / budget * 100, 1) if budget else 0.0

    # jours d'entraînement consécutifs jusqu'à hier (run/crossfit/strength)
    trained = {s["session_date"] for s in done
               if s["discipline"] in ("run", "crossfit", "strength")}
    days_since_rest = 0
    cur = day - timedelta(days=1)
    for _ in range(14):
        if cur.isoformat() in trained:
            days_since_rest += 1
            cur -= timedelta(days=1)
        else:
            break

    # ACWR : charge aiguë 7j vs charge chronique hebdo moyenne sur 28j.
    # Tant que la base chronique est trop courte (< 21 j d'historique), l'ACWR
    # n'est pas fiable → on l'affiche comme "insuffisant" plutôt que d'alarmer.
    acute = store.sessions.stress_units_between(
        _aid(), (day - timedelta(days=7)).isoformat(), payload["date"])
    chronic_total = store.sessions.stress_units_between(
        _aid(), (day - timedelta(days=28)).isoformat(), payload["date"])
    earliest = min((s["session_date"] for s in done), default=payload["date"])
    history_days = (day - date.fromisoformat(earliest)).days
    if history_days < 21:
        acwr_val, acwr_label = round(acute / (chronic_total / 4), 2) if chronic_total else 0.0, "insufficient_history"
    else:
        acwr_val, acwr_label = coach.acwr(acute, chronic_total / 4)

    return {
        "last_two_disciplines": last_two,
        "budget_consumed_pct": budget_pct,
        "days_since_rest": days_since_rest,
        "_meta": {"week_type": week_type, "consumed_su": round(consumed, 1),
                  "budget_su": budget, "acute_7d_su": round(acute, 1),
                  "acwr": acwr_val, "acwr_label": acwr_label},
    }


@app.post("/coach/session")
def coach_session(body: SessionTodayIn) -> dict:
    # on retire les champs None pour laisser le planning (date) ou les défauts agir
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    adaptive = _adaptive_context(payload)
    meta = adaptive.pop("_meta", {})
    for k, v in adaptive.items():
        payload.setdefault(k, v)  # l'override explicite du client est prioritaire
    cfg = _schedule_config()
    # Sommeil court (< 6 h) → intensité du jour plafonnée : la privation de
    # sommeil dégrade performance, coordination et récupération (Fullagar
    # 2015) — on garde le volume facile, on coupe le très intense.
    sleep_h = payload.pop("sleep_hours", None)
    result = _safe(lambda p: coach.session_today(p, cfg), payload)
    if sleep_h is not None and float(sleep_h) < 6:
        cap = 6.0 if float(sleep_h) >= 5 else 5.0
        if float(result.get("intensity_cap") or 10) > cap:
            result["intensity_cap"] = cap
        notes = result.setdefault("safety_notes", [])
        notes.insert(0, f"Sommeil {sleep_h:g} h : intensité plafonnée à RPE {cap:g} "
                        "aujourd'hui — garde le volume facile, coupe le très intense.")
    result["context"] = {
        "budget_consumed_pct": payload.get("budget_consumed_pct", 0),
        "days_since_rest": payload.get("days_since_rest", 0),
        "last_two_disciplines": payload.get("last_two_disciplines", []),
        **meta,
    }
    return result


@app.post("/coach/weekly-budget")
def weekly_budget(body: WeeklyBudgetIn) -> dict:
    return _safe(coach.weekly_budget, body.model_dump())


@app.post("/schedule/day")
def schedule_day(body: ScheduleIn) -> dict:
    cfg = _schedule_config()
    return _safe(lambda p: coach.schedule_day(p, cfg), body.model_dump())


@app.post("/schedule/week")
def schedule_week(body: ScheduleIn) -> dict:
    cfg = _schedule_config()
    return _safe(lambda p: coach.schedule_week(p, cfg), body.model_dump())


class SchedulePhaseIn(BaseModel):
    """« Cette semaine est ma GRANDE (is_big_week=true) / PETITE semaine »."""
    is_big_week: bool
    reference_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


@app.post("/schedule/phase")
def set_schedule_phase(body: SchedulePhaseIn) -> dict:
    """Recale la PHASE du rythme 3/2/2/3 sur la réalité de l'athlète (l'ancre
    stockée peut être décalée d'une semaine après un changement de service ou
    un redémarrage de programme). La progression 5/3/1 est PRÉSERVÉE : le J0
    courant est figé dans `start_monday` avant de bouger l'ancre — recaler son
    planning de service ne doit pas décaler son cycle de force."""
    cfg = _schedule_config()
    if cfg.get("type") != "police_3223":
        raise HTTPException(
            status_code=409,
            detail="Rythme hebdomadaire : aucune phase 3/2/2/3 à recaler.")
    ref = _date.fromisoformat(body.reference_date) if body.reference_date else _date.today()
    keep_start = _us.plan_start(cfg).isoformat()   # J0 5/3/1 AVANT déplacement
    ws = {**cfg,
          "anchor_big_week_monday": _us.anchor_for_current_week(body.is_big_week, ref),
          "start_monday": keep_start}
    store.athletes.update_profile(_aid(), work_schedule=_us.normalize(ws))
    new_cfg = _schedule_config()
    return {"profile": store.profile_payload(_aid()),
            "week_type": _us.week_type_for(new_cfg, ref),
            "week": _us.week_schedule(new_cfg, ref)}


@app.post("/roadmap")
def roadmap(body: RoadmapIn) -> dict:
    return _safe(coach.roadmap, body.model_dump())


@app.get("/plan/annual")
def plan_annual() -> dict:
    """Squelette annuel : macro-périodisation BASE/BUILD/PEAK/TRANSITION → 2029."""
    return coach.annual_plan()


def _standby_state() -> dict:
    """État standby de l'athlète (replié paresseusement si une pause est passée)."""
    row = store.standby.get(_aid()) or {}
    folded, changed = _standby.fold_if_complete(row, _date.today())
    if changed:
        store.standby.set_window(
            _aid(), folded.get("mode"), folded.get("start_date"),
            folded.get("end_date"), None, int(folded.get("plan_shift_weeks") or 0))
    return folded


def _resolve_day(date_iso: str, vma: float | None, fcmax: int | None) -> dict:
    return _standby.planned_day(date_iso, _standby_state(), _schedule_config(),
                                vma or 14.0, fcmax or 186, _strength_maxes())


@app.get("/plan/weekly")
def plan_weekly(from_week: int = 0, n: int = 6,
                vma: float | None = None, fcmax: int | None = None) -> dict:
    """Mission 1B — N semaines détaillées jour par jour (course/force/WOD/natation),
    calées sur le 3/2/2/3 et tenant compte du mode standby/vacances."""
    cfg = _schedule_config()
    maxes = _strength_maxes()
    base = coach.weekly_plan(from_week, n, vma, fcmax, cfg, maxes)
    state = _standby_state()
    for wk in base["weeks"]:
        for i, day in enumerate(wk["days"]):
            wk["days"][i] = _standby.planned_day(day["date"], state, cfg,
                                                 vma or 14.0, fcmax or 186, maxes)
    return base


@app.get("/plan/day")
def plan_day(date: str, vma: float | None = None, fcmax: int | None = None) -> dict:
    """Séances planifiées pour une date — MÊME source que /plan/weekly (mêmes
    seeds par semaine/jour), avec prise en compte du mode standby. Garantit que
    l'écran Jour, l'onglet Séances et l'Agenda affichent une séance identique."""
    if not _DATE_RE.match(date or ""):
        raise HTTPException(status_code=422, detail="date attendue au format YYYY-MM-DD")
    return _resolve_day(date, vma, fcmax)


# ---------- Mode standby / vacances (par athlète) ----------
@app.get("/standby")
def get_standby() -> dict:
    st = _standby_state()
    params = st.get("params_json")
    if isinstance(params, str) and params:
        try:
            params = json.loads(params)
        except (ValueError, TypeError):
            params = {}
    return {"mode": st.get("mode"), "start_date": st.get("start_date"),
            "end_date": st.get("end_date"), "params": params or {},
            "plan_shift_weeks": int(st.get("plan_shift_weeks") or 0)}


@app.post("/standby")
def set_standby(body: StandbyIn) -> dict:
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date avant start_date")
    base = int(_standby_state().get("plan_shift_weeks") or 0)
    params = {"sessions_per_day": body.sessions_per_day, "equipment": body.equipment}
    store.standby.set_window(_aid(), body.mode, body.start_date,
                             body.end_date, params, base)
    return get_standby()


@app.delete("/standby")
def clear_standby() -> dict:
    base = int(_standby_state().get("plan_shift_weeks") or 0)
    store.standby.set_window(_aid(), None, None, None, None, base)
    return get_standby()


@app.get("/generate/run")
def generate_run_ep(type: str, seed: int = 1, vma: float | None = None,
                    fcmax: int | None = None, sciatic: bool = True) -> dict:
    """Mission 2 — séance de course unique (déterministe par type+seed).
    Types : vma_courte, vma_longue, seuil, fartlek, tempo, z2, cotes."""
    try:
        return coach.generate_run(type, seed, vma, fcmax, sciatic)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/generate/run/library")
def run_library_ep(vma: float | None = None, fcmax: int | None = None) -> dict:
    """Mission 2 — 700 séances (100 par type) : seed, titre, difficulté, durée."""
    return coach.run_library(vma, fcmax)


@app.get("/generate/mobility")
def generate_mobility_ep(focus: str = "full", duration_min: int = 12,
                         seed: int = 1, moment: str = "soir") -> dict:
    """Routine mobilité (style GOWOD) : focus ciblé, minutée, sciatique-safe.
    moment='avant' → dynamique uniquement (pré-séance)."""
    return _gen_mobility(focus, max(6, min(30, duration_min)), max(1, seed),
                         True, "avant" if moment == "avant" else "soir")


class WodGenIn(BaseModel):
    format: str = "auto"   # auto | amrap | for_time | emom | death_by | chipper | ...
    duration_min: int = Field(default=12, ge=4, le=30)
    seed: str = "wod"
    exclude_lumbar: bool = True   # règle sciatique L5-S1, ON par défaut
    bodyweight: bool = False      # PDC : poids du corps uniquement (sans matériel)
    team_size: int = Field(default=1, ge=1, le=4)   # WOD team / partenaire


@app.post("/generate/wod")
def generate_wod_ep(body: WodGenIn) -> dict:
    """Mission 3 — WOD complet (15 formats, charges/distances fixes, cohérence lombaire)."""
    return _safe(coach.generate_wod, body.model_dump())


@app.get("/generate/wod/random")
def random_wod_ep(exclude_lumbar: bool = True) -> dict:
    """Mission 3 — WOD aléatoire (seed + format aléatoires)."""
    return coach.random_wod(exclude_lumbar)


@app.get("/generate/strength")
def strength_531_ep(day: str, week: int = 1, cycle: int = 0) -> dict:
    """Mission 4 — séance force 5/3/1 (Push/Pull/Legs) calée sur les 1RM de
    l'utilisateur : Big 3 McGill, principal au cycle courant, accessoires, finisher."""
    try:
        return coach.strength_531(day, week, cycle, _strength_maxes())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/strength/cycle")
def strength_cycle_ep(cycle: int = 0) -> dict:
    """Mission 4 — vue du cycle 4 semaines × 3 jours + Training Max courants."""
    return coach.strength_cycle(cycle, _strength_maxes())


@app.get("/strength/progression")
def strength_progression_ep(lift: str = "bench", cycles: int = 6) -> dict:
    """Projection des charges (top set + 1RM estimé) sur N cycles."""
    try:
        return coach.strength_progression(lift, cycles, _strength_maxes())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/generate")
def generate(body: GenerateIn) -> dict:
    """Bouton 'Générer une séance' propre à chaque page (course/force/wod).
    Indépendant de la décision du jour et des données montre."""
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return _safe(coach.generate_discipline, payload)


@app.post("/coach/arbitrate-goals")
def arbitrate_goals(body: GoalsIn) -> dict:
    return _safe(coach.arbitrate_goals, body.model_dump())


@app.post("/run/hr-profile")
def hr_profile(body: HRProfileIn) -> dict:
    return _safe(coach.hr_profile, body.model_dump())


@app.post("/run/predictions")
def run_predictions(body: PredictionIn) -> dict:
    return _safe(coach.run_predictions, body.model_dump())


@app.post("/run/pace-table")
def pace_table(body: PaceTableIn) -> dict:
    return _safe(coach.pace_table, body.model_dump())


@app.post("/strength/generate")
def strength_generate(body: StrengthSessionIn) -> dict:
    return _safe(coach.generate_strength_session, body.model_dump())


@app.post("/strength/pr-estimate")
def pr_estimate(body: PRIn) -> dict:
    return _safe(coach.pr_estimate, body.model_dump())


@app.post("/raid/strength-report")
def raid_strength_report(body: RaidStrengthIn) -> dict:
    return _safe(coach.raid_strength_report, body.model_dump())


@app.post("/plans/auto-generate")
def auto_plan(body: AutoPlanIn) -> dict:
    return _safe(coach.auto_plan, body.model_dump())


def _activity_from_plan(date: str) -> tuple[str, str]:
    """Niveau d'activité dérivé des séances RÉELLEMENT planifiées ce jour
    (plan de l'athlète, standby inclus) → périodisation glucidique automatique
    « fuel for the work required » (Impey et al. 2018)."""
    day = _resolve_day(date, None, None)
    mains = [s for s in day.get("sessions", []) if s.get("type") != "recovery"]
    hard = {"strength", "crossfit"}
    hard_run = ("vma", "seuil", "cotes", "fartlek", "tempo")
    n_hard = sum(1 for s in mains
                 if s.get("type") in hard
                 or (s.get("type") == "run" and any(k in str(s.get("title", "")).lower() for k in hard_run)))
    if not mains:
        return "rest", "jour de repos → low carb"
    if len(mains) >= 2:
        return "high", "double séance → high carb"
    if n_hard:
        return "moderate", "séance qualité → medium carb"
    return "light", "séance facile (Z2/natation) → medium carb léger"


@app.post("/nutrition/daily-macros")
def daily_macros(body: MacrosIn) -> dict:
    payload = body.model_dump()
    if payload["target_weight_kg"] is None:
        payload["target_weight_kg"] = payload["weight_kg"]
    auto_reason = None
    date = payload.pop("date", None)
    if date:
        try:
            payload["activity"], auto_reason = _activity_from_plan(date)
        except Exception:   # noqa: BLE001 — plan indisponible → activité fournie
            pass
    res = _safe(coach.daily_macros, payload)
    if auto_reason:
        res["auto_activity"] = {"activity": payload["activity"], "reason": auto_reason}
    # Répartition protéique par repas (Schoenfeld & Aragon 2018 : ~0,4 g/kg
    # par repas × 4 prises maximise la synthèse protéique) + timing
    # péri-entraînement (ISSN 2017, Kerksick et al.).
    w = float(payload["weight_kg"])
    per_meal = round(0.4 * w)
    res["meal_distribution"] = {
        "meals": 4,
        "protein_per_meal_g": per_meal,
        "note": (f"Vise ~{per_meal} g de protéines × 4 prises (matin, midi, "
                 "post-séance, soir) plutôt qu'un gros repas — meilleure "
                 "synthèse musculaire à quota égal."),
    }
    res["peri_workout"] = {
        "avant": "1-2 h avant séance clé : 1-2 g/kg de glucides digestes + protéines légères.",
        "apres": f"Dans les 2 h : {per_meal}-{per_meal + 10} g protéines + glucides (1 g/kg si 2 séances le même jour).",
        "double_seance": "Jour à 2 séances : la fenêtre glucidique post-séance 1 conditionne la qualité de la séance 2.",
    }
    return res


@app.post("/nutrition/selection-day")
def selection_day(body: WeightIn) -> dict:
    return _safe(coach.selection_day_nutrition, body.model_dump())


# ---------- Nutrition+ (compléments, aliments→grammes, synergies, garde-fous) ----------
class PortionsIn(BaseModel):
    target_p: float = Field(ge=0, le=400)
    target_c: float = Field(ge=0, le=800)
    target_f: float = Field(ge=0, le=300)
    protein_id: str = "poulet"
    carb_id: str = "rizcuit"
    fat_id: str = "huileolive"


class GuardrailsIn(BaseModel):
    weight_kg: float = Field(ge=40, le=180)
    calories: int = Field(ge=800, le=8000)
    protein_g: float = Field(ge=0, le=400)
    fat_g: float = Field(ge=0, le=300)
    body_fat_pct: float | None = Field(default=None, ge=3, le=50)
    exercise_kcal: int = Field(default=500, ge=0, le=4000)


@app.get("/nutrition/supplements")
def nutrition_supplements(session_type: str = "rest") -> dict:
    return coach.nutrition_supplements(session_type)


@app.get("/nutrition/foods")
def nutrition_foods() -> dict:
    return coach.nutrition_foods()


@app.get("/nutrition/synergies")
def nutrition_synergies() -> dict:
    return coach.nutrition_synergies()


@app.post("/nutrition/portions")
def nutrition_portions(body: PortionsIn) -> dict:
    return _safe(coach.nutrition_portions, body.model_dump())


@app.post("/nutrition/guardrails")
def nutrition_guardrails(body: GuardrailsIn) -> dict:
    return _safe(coach.nutrition_guardrails, body.model_dump())


# ---------- Persistance (B13) — endpoints d'écriture utilisés par l'app mobile ----------
@app.post("/metrics/record")
def record_metrics(body: MetricsRecordIn) -> dict:
    data = body.model_dump(exclude_none=True)
    metric_date = data.pop("date")
    data["pain_flag"] = int(body.pain_flag)
    data["sciatic_flare"] = int(body.sciatic_flare)
    store.metrics.upsert(_aid(), metric_date, **data)
    return {"status": "recorded", "date": metric_date}


@app.post("/sessions/complete")
def complete_session(body: SessionCompleteIn) -> dict:
    # charge (SU) calculée serveur si non fournie → cohérente avec budget/ACWR
    su = body.stress_units or coach.compute_su(body.duration_min, body.intensity_rpe)
    session_id = store.sessions.record(
        _aid(), body.discipline, body.session_date,
        body.duration_min, body.intensity_rpe, su,
        body.detail, status="done",
        family_id=body.family_id, template_id=body.template_id)
    if body.feedback:
        store.sessions.complete(session_id, body.feedback)
    return {"status": "recorded", "session_id": session_id}


@app.post("/sessions/save")
def save_session(body: SessionSaveIn) -> dict:
    """Persiste une séance générée (planifiée pour une date, ou marquée faite)
    → visible dans l'historique et l'agenda. SU calculées si 'done'."""
    su = coach.compute_su(body.duration_min, body.intensity_rpe) if body.status == "done" else 0.0
    metrics = {k: v for k, v in {
        "distance_km": body.distance_km, "hr_avg": body.hr_avg, "hr_max": body.hr_max,
        "elevation_m": body.elevation_m, "calories": body.calories, "avg_pace": body.avg_pace,
        "te_aerobic": body.te_aerobic, "te_anaerobic": body.te_anaerobic,
        "cadence_spm": body.cadence_spm,
    }.items() if v is not None}
    detail = dict(body.detail or {})
    if metrics:
        detail["metrics"] = {**detail.get("metrics", {}), **metrics}
    if body.performed:
        detail["performed"] = body.performed
    # Autorégulation 1RM (Helms 2016) : si la série max loggée donne un 1RM
    # estimé au-dessus du 1RM enregistré, on PROPOSE la mise à jour (1 clic
    # côté app) — jamais automatique (une très bonne journée n'est pas un max).
    rm_suggestion = None
    for entry in _performed_entries(body.performed):
        est = float(entry.get("est_1rm") or 0)
        key = _lift_key_of(str(entry.get("lift") or ""))
        if not key or est <= 0:
            continue
        current = _strength_maxes().get(key)
        if current is None or est > float(current) + 1.0:
            from engines.strength_531.engine import TRAINING_MAX as _TM
            rm_suggestion = {
                "lift_key": key, "lift_name": _TM[key]["name"],
                "current_1rm": float(current) if current is not None else None,
                "estimated_1rm": round(est * 2) / 2,
            }
            break
    # WOD chronométré : libellé de score + commentaire honnête de performance,
    # comparés aux tentatives précédentes (même format en priorité).
    assessment = None
    res = detail.get("result")
    if isinstance(res, dict) and res.get("mode") in ("for_time", "amrap"):
        detail.setdefault("score_label", _wod_scoring.score_label(res))
        assessment = _wod_scoring.assess(
            {**res, "format_key": detail.get("format_key")}, _wod_history(_aid()))
        detail["assessment"] = assessment
    # Idempotent : re-marquer faite la MÊME séance (même date + discipline +
    # titre) met à jour la ligne existante au lieu de créer un doublon. Une
    # autre séance du même jour (CAP matin puis force soir) → ligne séparée.
    if body.status == "done":
        existing = store.sessions.find_done(
            _aid(), body.session_date, body.discipline, body.title)
        if existing is not None:
            store.sessions.update_done(
                existing, body.duration_min, body.intensity_rpe, su, detail)
            return {"status": "updated", "session_id": existing,
                    "persisted_status": "done", "rm_suggestion": rm_suggestion,
                    "assessment": assessment}
    session_id = store.sessions.record(
        _aid(), body.discipline, body.session_date,
        body.duration_min, body.intensity_rpe, su,
        detail, status=body.status, family_id=body.title)
    return {"status": "saved", "session_id": session_id,
            "persisted_status": body.status, "rm_suggestion": rm_suggestion,
            "assessment": assessment}


@app.post("/sessions/manual")
def manual_session(body: ManualSessionIn) -> dict:
    """Séance LIBRE hors plan (vélo, boxe, JJB, natation…) → enregistrée comme
    FAITE et comptée dans le suivi (charge/ACWR, agenda, historique)."""
    su = coach.compute_su(body.duration_min, body.intensity_rpe)
    detail = {"activity": body.activity, "manual": True,
              "distance_km": body.distance_km, "hr_avg": body.hr_avg,
              "hr_max": body.hr_max, "elevation_m": body.elevation_m,
              "calories": body.calories, "notes": body.notes}
    session_id = store.sessions.record(
        _aid(), body.discipline, body.session_date,
        body.duration_min, body.intensity_rpe, su,
        detail, status="done", family_id=body.activity)
    return {"status": "recorded", "session_id": session_id}


@app.post("/benchmarks/record")
def record_benchmark(body: BenchmarkRecordIn) -> dict:
    bench_id = store.benchmarks.record(
        _aid(), body.benchmark_id, body.result_value,
        body.result_unit, body.test_date, body.detail)
    return {"status": "recorded", "id": bench_id}


# ---------- Garmin Connect (OAuth 1.0a serveur) ----------
@app.get("/garmin/status")
def garmin_status() -> dict:
    return {"configured": garmin.is_configured(),
            "connected": garmin_tokens.is_connected(_aid())}


@app.get("/garmin/connect")
def garmin_connect() -> dict:
    if not garmin.is_configured():
        raise HTTPException(status_code=503,
                            detail="Garmin non configuré (clés API manquantes côté serveur).")
    try:
        authorize_url, token, secret = garmin.start_oauth()
    except Exception as e:  # noqa: BLE001 — erreurs réseau/OAuth → message clair
        raise HTTPException(status_code=502, detail=f"Garmin OAuth: {e}")
    garmin_tokens.save_request_token(_aid(), token, secret)
    return {"authorize_url": authorize_url}


@app.get("/garmin/callback")
def garmin_callback(oauth_token: str, oauth_verifier: str) -> HTMLResponse:
    row = garmin_tokens.get(_aid())
    if not row or row.get("request_token") != oauth_token:
        return HTMLResponse("<h2>Lien d'autorisation expiré. Relance la connexion.</h2>",
                            status_code=400)
    try:
        access_token, access_secret = garmin.complete_oauth(
            oauth_token, row["request_token_secret"], oauth_verifier)
    except Exception as e:  # noqa: BLE001
        return HTMLResponse(f"<h2>Échec de connexion Garmin: {e}</h2>", status_code=502)
    garmin_tokens.save_access_token(_aid(), access_token, access_secret)
    return HTMLResponse(
        "<h2>✅ Montre Garmin connectée</h2><p>Tu peux fermer cette page et "
        "revenir dans l'app, puis lancer une synchronisation.</p>")


@app.post("/garmin/sync")
def garmin_sync() -> dict:
    row = garmin_tokens.get(_aid())
    if not row or not row.get("access_token"):
        raise HTTPException(status_code=400, detail="Garmin non connecté.")
    day = _date.today().isoformat()
    try:
        wellness = garmin.fetch_wellness(row["access_token"], row["access_token_secret"], day)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Garmin sync: {e}")
    metrics = garmin.map_to_metrics(wellness)
    if metrics:
        store.metrics.upsert(_aid(), day, **metrics)
    return {"status": "synced", "date": day, "metrics": metrics}


@app.post("/garmin/disconnect")
def garmin_disconnect() -> dict:
    garmin_tokens.disconnect(_aid())
    return {"status": "disconnected"}


@app.get("/metrics/latest")
def latest_metrics() -> dict:
    row = store.metrics.latest(_aid())
    return row or {}


@app.get("/benchmarks/{benchmark_id}/progression")
def benchmark_progression(benchmark_id: str) -> dict:
    return {"benchmark_id": benchmark_id,
            "results": store.benchmarks.progression(_aid(), benchmark_id)}


# ---------- Profil athlète ----------
@app.get("/profile")
def get_profile() -> dict:
    return store.profile_payload(_aid())


@app.patch("/profile")
def update_profile(body: ProfileUpdateIn) -> dict:
    fields = body.model_dump(exclude_none=True)
    if "work_schedule" in fields:  # normalise le rythme avant stockage
        fields["work_schedule"] = _us.normalize(fields["work_schedule"])
    if fields:
        store.athletes.update_profile(_aid(), **fields)
    return store.profile_payload(_aid())


# ---------- Historique d'entraînement ----------
@app.get("/sessions/recent")
def recent_sessions(n: int = 30) -> dict:
    n = max(1, min(n, 200))
    rows = store.sessions.last_n(_aid(), n)
    # Expose le score d'un WOD chronométré (temps/reps) pour le suivi, sans
    # forcer le client à reparser tout le detail_json.
    for s in rows:
        score = _wod_score(_detail_of(s))
        if score:
            s["score"] = score
    return {"sessions": rows}


class WodScoreIn(BaseModel):
    """Score d'un WOD saisi ou corrigé à la main (chrono, ou depuis l'agenda)."""
    mode: str = Field(pattern="^(for_time|amrap)$")
    time_sec: int = Field(default=0, ge=0, le=36000)
    reps: int = Field(default=0, ge=0, le=100000)
    rounds: int | None = Field(default=None, ge=0, le=1000)
    distance_m: int | None = Field(default=None, ge=0, le=200000)
    capped: bool = False
    cap_sec: int = Field(default=0, ge=0, le=36000)
    notes: str | None = Field(default=None, max_length=500)


def _wod_history(aid: int, exclude_id: int | None = None) -> list[dict]:
    """Résultats de WOD passés (du plus ancien au plus récent) pour comparer."""
    out = []
    for s in reversed(store.sessions.last_n(aid, 120)):
        if s["status"] != "done" or s["discipline"] != "crossfit":
            continue
        if exclude_id is not None and s["id"] == exclude_id:
            continue
        det = _detail_of(s) or {}
        res = det.get("result")
        if isinstance(res, dict) and res.get("mode") in ("for_time", "amrap"):
            out.append({**res, "format_key": det.get("format_key")})
    return out


@app.patch("/sessions/{session_id}/score")
def update_session_score(session_id: int, body: WodScoreIn) -> dict:
    """Saisit/corrige le score d'un WOD déjà enregistré (agenda → suivi), et
    renvoie un commentaire honnête de performance."""
    row = store.sessions.get(_aid(), session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Séance introuvable.")
    if row["discipline"] != "crossfit":
        raise HTTPException(status_code=409,
                            detail="Seules les séances CrossFit ont un score de WOD.")
    detail = dict(_detail_of(row) or {})
    result = {k: v for k, v in body.model_dump().items() if v is not None}
    detail["result"] = result
    detail["score_label"] = _wod_scoring.score_label(result)
    assessment = _wod_scoring.assess(
        {**result, "format_key": detail.get("format_key")},
        _wod_history(_aid(), exclude_id=session_id))
    detail["assessment"] = assessment
    # Le temps réel du WOD fait la durée de séance (et donc la charge).
    dur = max(1, round(body.time_sec / 60)) if body.time_sec else int(row["duration_min"] or 1)
    rpe = float(row["intensity_rpe"] or 9)
    su = coach.compute_su(dur, rpe)
    store.sessions.update_done(session_id, dur, rpe, su, detail)
    return {"status": "updated", "session_id": session_id,
            "score_label": detail["score_label"], "assessment": assessment}


@app.delete("/sessions/{session_id}")
def delete_session(session_id: int) -> dict:
    """Supprime une séance enregistrée (annule une mauvaise manip). Ne supprime
    que si elle appartient à l'utilisateur courant. Invalide les caches agenda."""
    ok = store.sessions.delete(_aid(), session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Séance introuvable.")
    return {"status": "deleted", "session_id": session_id}


# ---------- Agenda prévisionnel (planning + intention + séances réalisées) ----------
@app.post("/agenda/week")
def agenda_week(body: ScheduleIn) -> dict:
    week = coach.schedule_week(body.model_dump(), _schedule_config())
    # Plusieurs séances peuvent partager une date (ex. CAP le matin + force le
    # soir) : on renvoie TOUTES les séances du jour dans done_all (faites en
    # premier, puis planifiées, ordre chrono d'enregistrement), et on garde
    # done = la plus pertinente (une 'done' l'emporte sur une 'planned') pour
    # compatibilité. Rien n'est écrasé : chaque séance faite reste au suivi.
    by_date: dict[str, list[dict]] = {}
    for s in store.sessions.last_n(_aid(), 120):
        by_date.setdefault(s["session_date"], []).append(s)

    def _entry(rec: dict) -> dict:
        det = _detail_of(rec)
        score = _wod_score(det)
        return {"id": rec["id"], "discipline": rec["discipline"],
                "duration_min": rec["duration_min"],
                "status": rec["status"], "title": rec.get("family_id"),
                "score_label": score["label"] if score else None,
                "metrics": det.get("metrics"),
                "performed": det.get("performed"),
                # WOD : score courant + commentaire → édition depuis l'agenda.
                "wod_result": det.get("result") if rec["discipline"] == "crossfit" else None,
                "assessment": det.get("assessment")}

    for day in week["days"]:
        recs = by_date.get(day["date"], [])
        # faites d'abord, puis planifiées ; à statut égal ordre d'enregistrement
        recs = sorted(recs, key=lambda r: (r["status"] != "done", r["id"]))
        entries = [_entry(r) for r in recs]
        day["done_all"] = entries
        day["done"] = entries[0] if entries else None
    return week


# ---------- Coach Chat (LLM Claude si clé dispo, sinon déterministe) ----------
@app.post("/coach/chat")
def coach_chat(body: ChatIn) -> dict:
    ctx = _chat_context(body.date)
    if _coach_llm_enabled():
        reply = _coach_llm(body.message, ctx, body.history)
        if reply:
            return {"reply": reply, "topic": "coach",
                    "suggestions": [], "source": "llm"}
    # repli : moteur déterministe (hors-ligne / pas de clé / erreur API)
    res = _coach_chat_answer(body.message, ctx)
    res["source"] = "rules"
    return res


# ---------- Tableau de bord analytics (dérivé des données enregistrées) ----------
@app.get("/analytics/snapshot")
def analytics_snapshot() -> dict:
    return _analytics_from_store()
