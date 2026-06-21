"""RAID Coach API — FastAPI application.
Run: uvicorn api.main:app --reload
Docs auto-générées: http://localhost:8000/docs
"""
from __future__ import annotations

import os
from datetime import date as _date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from api import garmin
from api.garmin import GarminTokenStore
from api.persistence import Store
from api.services.coach_api import CoachAPI
from engines.coach_chat import answer as _coach_chat_answer
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


def _chat_context(for_date: str | None) -> dict:
    """Assemble le contexte du coach (profil, métriques du jour, planning) depuis
    le store pour personnaliser la réponse du chat."""
    ctx: dict = {"profile": store.profile_payload()}
    latest = store.metrics.latest(store.athlete_id)
    if latest:
        ctx["metrics"] = latest
    try:
        day = for_date or _date.today().isoformat()
        ctx["today"] = coach.schedule_day({"date": day})
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


def _analytics_from_store() -> dict:
    """Dérive un instantané analytics des séances et métriques enregistrées.
    Renvoie un statut 'warming_up' tant que l'historique est trop court."""
    sessions = store.sessions.last_n(store.athlete_id, 28)
    loads = [float(s["stress_units"] or 0) for s in sessions if s["status"] == "done"]
    metrics = store.db.query(
        """SELECT readiness, fatigue, sleep_quality FROM daily_metrics
           WHERE athlete_id = ? ORDER BY metric_date DESC LIMIT 14""",
        (store.athlete_id,))
    readiness = [float(m["readiness"]) for m in metrics if m["readiness"] is not None]
    recovery = [100.0 - float(m["fatigue"]) for m in metrics if m["fatigue"] is not None]

    if len(loads) < 3 or len(readiness) < 3:
        return {"status": "warming_up",
                "message": "Pas encore assez de données — enregistre quelques séances et check-ins.",
                "sessions_logged": len(loads), "metrics_logged": len(readiness)}

    chronic = sum(loads) / len(loads)
    data = AnalyticsInput(
        recent_loads=loads[:7], chronic_load=chronic,
        readiness_scores=readiness, recovery_scores=recovery,
        performance_scores=readiness,  # proxy en l'absence de score perf dédié
        weakness_scores={})
    r = coach.analytics.analyze(data)
    return {
        "status": r.global_status,
        "fitness": round(r.fitness.score, 1),
        "fatigue": round(r.fatigue.score, 1),
        "acwr": round(r.fatigue.acute_chronic_ratio, 2),
        "readiness": round(r.readiness.score, 1),
        "readiness_trend": r.readiness.trend.value,
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
    week_type = coach.schedule_day({"date": payload["date"]})["week_type"]
    monday = (day - timedelta(days=day.weekday())).isoformat()
    yesterday = (day - timedelta(days=1)).isoformat()

    done = [s for s in store.sessions.last_n(store.athlete_id, 40) if s["status"] == "done"]
    last_two = [s["discipline"] for s in done[:2]]

    consumed = store.sessions.stress_units_between(store.athlete_id, monday, payload["date"])
    budget = coach.weekly_budget_su(week_type)
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
        store.athlete_id, (day - timedelta(days=7)).isoformat(), payload["date"])
    chronic_total = store.sessions.stress_units_between(
        store.athlete_id, (day - timedelta(days=28)).isoformat(), payload["date"])
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
    result = _safe(coach.session_today, payload)
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
    return _safe(coach.schedule_day, body.model_dump())


@app.post("/schedule/week")
def schedule_week(body: ScheduleIn) -> dict:
    return _safe(coach.schedule_week, body.model_dump())


@app.post("/roadmap")
def roadmap(body: RoadmapIn) -> dict:
    return _safe(coach.roadmap, body.model_dump())


@app.get("/plan/annual")
def plan_annual() -> dict:
    """Squelette annuel : macro-périodisation BASE/BUILD/PEAK/TRANSITION → 2029."""
    return coach.annual_plan()


@app.get("/plan/weekly")
def plan_weekly(from_week: int = 0, n: int = 6,
                vma: float | None = None, fcmax: int | None = None) -> dict:
    """Mission 1B — N semaines détaillées jour par jour (course/force/WOD/natation)
    assemblées via les générateurs, calées sur le planning 3/2/2/3."""
    return coach.weekly_plan(from_week, n, vma, fcmax)


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


class WodGenIn(BaseModel):
    format: str = "auto"   # auto | amrap | for_time | emom | death_by | chipper | ...
    duration_min: int = Field(default=12, ge=4, le=30)
    seed: str = "wod"
    exclude_lumbar: bool = True   # règle sciatique L5-S1, ON par défaut


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
    """Mission 4 — séance force 5/3/1 (Push/Pull/Legs) : Big 3 McGill, mouvement
    principal au cycle courant, accessoires double-progression, finisher WOD."""
    try:
        return coach.strength_531(day, week, cycle)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/strength/cycle")
def strength_cycle_ep(cycle: int = 0) -> dict:
    """Mission 4 — vue du cycle 4 semaines × 3 jours + Training Max courants."""
    return coach.strength_cycle(cycle)


@app.get("/strength/progression")
def strength_progression_ep(lift: str = "bench", cycles: int = 6) -> dict:
    """Projection des charges (top set + 1RM estimé) sur N cycles."""
    try:
        return coach.strength_progression(lift, cycles)
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


@app.post("/nutrition/daily-macros")
def daily_macros(body: MacrosIn) -> dict:
    payload = body.model_dump()
    if payload["target_weight_kg"] is None:
        payload["target_weight_kg"] = payload["weight_kg"]
    return _safe(coach.daily_macros, payload)


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
    store.metrics.upsert(store.athlete_id, metric_date, **data)
    return {"status": "recorded", "date": metric_date}


@app.post("/sessions/complete")
def complete_session(body: SessionCompleteIn) -> dict:
    # charge (SU) calculée serveur si non fournie → cohérente avec budget/ACWR
    su = body.stress_units or coach.compute_su(body.duration_min, body.intensity_rpe)
    session_id = store.sessions.record(
        store.athlete_id, body.discipline, body.session_date,
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
    session_id = store.sessions.record(
        store.athlete_id, body.discipline, body.session_date,
        body.duration_min, body.intensity_rpe, su,
        body.detail, status=body.status, family_id=body.title)
    return {"status": "saved", "session_id": session_id, "persisted_status": body.status}


@app.post("/benchmarks/record")
def record_benchmark(body: BenchmarkRecordIn) -> dict:
    bench_id = store.benchmarks.record(
        store.athlete_id, body.benchmark_id, body.result_value,
        body.result_unit, body.test_date, body.detail)
    return {"status": "recorded", "id": bench_id}


# ---------- Garmin Connect (OAuth 1.0a serveur) ----------
@app.get("/garmin/status")
def garmin_status() -> dict:
    return {"configured": garmin.is_configured(),
            "connected": garmin_tokens.is_connected(store.athlete_id)}


@app.get("/garmin/connect")
def garmin_connect() -> dict:
    if not garmin.is_configured():
        raise HTTPException(status_code=503,
                            detail="Garmin non configuré (clés API manquantes côté serveur).")
    try:
        authorize_url, token, secret = garmin.start_oauth()
    except Exception as e:  # noqa: BLE001 — erreurs réseau/OAuth → message clair
        raise HTTPException(status_code=502, detail=f"Garmin OAuth: {e}")
    garmin_tokens.save_request_token(store.athlete_id, token, secret)
    return {"authorize_url": authorize_url}


@app.get("/garmin/callback")
def garmin_callback(oauth_token: str, oauth_verifier: str) -> HTMLResponse:
    row = garmin_tokens.get(store.athlete_id)
    if not row or row.get("request_token") != oauth_token:
        return HTMLResponse("<h2>Lien d'autorisation expiré. Relance la connexion.</h2>",
                            status_code=400)
    try:
        access_token, access_secret = garmin.complete_oauth(
            oauth_token, row["request_token_secret"], oauth_verifier)
    except Exception as e:  # noqa: BLE001
        return HTMLResponse(f"<h2>Échec de connexion Garmin: {e}</h2>", status_code=502)
    garmin_tokens.save_access_token(store.athlete_id, access_token, access_secret)
    return HTMLResponse(
        "<h2>✅ Montre Garmin connectée</h2><p>Tu peux fermer cette page et "
        "revenir dans l'app, puis lancer une synchronisation.</p>")


@app.post("/garmin/sync")
def garmin_sync() -> dict:
    row = garmin_tokens.get(store.athlete_id)
    if not row or not row.get("access_token"):
        raise HTTPException(status_code=400, detail="Garmin non connecté.")
    day = _date.today().isoformat()
    try:
        wellness = garmin.fetch_wellness(row["access_token"], row["access_token_secret"], day)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Garmin sync: {e}")
    metrics = garmin.map_to_metrics(wellness)
    if metrics:
        store.metrics.upsert(store.athlete_id, day, **metrics)
    return {"status": "synced", "date": day, "metrics": metrics}


@app.post("/garmin/disconnect")
def garmin_disconnect() -> dict:
    garmin_tokens.disconnect(store.athlete_id)
    return {"status": "disconnected"}


@app.get("/metrics/latest")
def latest_metrics() -> dict:
    row = store.metrics.latest(store.athlete_id)
    return row or {}


@app.get("/benchmarks/{benchmark_id}/progression")
def benchmark_progression(benchmark_id: str) -> dict:
    return {"benchmark_id": benchmark_id,
            "results": store.benchmarks.progression(store.athlete_id, benchmark_id)}


# ---------- Profil athlète ----------
@app.get("/profile")
def get_profile() -> dict:
    return store.profile_payload()


@app.patch("/profile")
def update_profile(body: ProfileUpdateIn) -> dict:
    fields = body.model_dump(exclude_none=True)
    if fields:
        store.athletes.update_profile(store.athlete_id, **fields)
    return store.profile_payload()


# ---------- Historique d'entraînement ----------
@app.get("/sessions/recent")
def recent_sessions(n: int = 30) -> dict:
    n = max(1, min(n, 200))
    return {"sessions": store.sessions.last_n(store.athlete_id, n)}


# ---------- Agenda prévisionnel (planning + intention + séances réalisées) ----------
@app.post("/agenda/week")
def agenda_week(body: ScheduleIn) -> dict:
    week = coach.schedule_week(body.model_dump())
    # Plusieurs séances peuvent partager une date (ex. course le matin + force
    # marquée faite ensuite). On garde la plus pertinente : une séance 'done'
    # l'emporte sur une 'planned', et à statut égal la plus récente (id le plus
    # élevé). last_n est trié par date DESC, id DESC → le premier vu pour une
    # date est déjà le plus récent ; on ne remplace que si on trouve un 'done'.
    best: dict[str, dict] = {}
    for s in store.sessions.last_n(store.athlete_id, 60):
        d = s["session_date"]
        cur = best.get(d)
        if cur is None:
            best[d] = s
        elif cur["status"] != "done" and s["status"] == "done":
            best[d] = s
    for day in week["days"]:
        rec = best.get(day["date"])
        day["done"] = ({"discipline": rec["discipline"], "duration_min": rec["duration_min"],
                        "status": rec["status"], "title": rec.get("family_id")} if rec else None)
    return week


# ---------- Coach Chat (assistant déterministe, sans LLM externe) ----------
@app.post("/coach/chat")
def coach_chat(body: ChatIn) -> dict:
    return _coach_chat_answer(body.message, _chat_context(body.date))


# ---------- Tableau de bord analytics (dérivé des données enregistrées) ----------
@app.get("/analytics/snapshot")
def analytics_snapshot() -> dict:
    return _analytics_from_store()
