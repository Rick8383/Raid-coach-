"""RAID Coach API — FastAPI application.
Run: uvicorn api.main:app --reload
Docs auto-générées: http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.persistence import Store
from api.services.coach_api import CoachAPI
# CoachAPI met engines/legacy sur sys.path à l'import → AnalyticsInput accessible
from build6_analytics_engine.models import AnalyticsInput  # noqa: E402

app = FastAPI(
    title="RAID Coach Elite+ API",
    version="1.0.0",
    description="Backend API exposant tous les moteurs RAID Coach (B3-B11)",
)
coach = CoachAPI()
store = Store()


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
    last_two_disciplines: list[str] = []
    budget_consumed_pct: float = Field(default=0, ge=0, le=200)
    days_since_rest: int = Field(default=0, ge=0)
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
    return {"status": "ok", "service": "raid-coach-api", "version": "1.0.0"}


@app.post("/coach/daily-decision")
def daily_decision(body: DailyDecisionIn) -> dict:
    return _safe(coach.daily_decision, body.model_dump())


@app.post("/coach/session")
def coach_session(body: SessionTodayIn) -> dict:
    # on retire les champs None pour laisser le planning (date) ou les défauts agir
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return _safe(coach.session_today, payload)


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
    session_id = store.sessions.record(
        store.athlete_id, body.discipline, body.session_date,
        body.duration_min, body.intensity_rpe, body.stress_units,
        body.detail, status="done",
        family_id=body.family_id, template_id=body.template_id)
    if body.feedback:
        store.sessions.complete(session_id, body.feedback)
    return {"status": "recorded", "session_id": session_id}


@app.post("/benchmarks/record")
def record_benchmark(body: BenchmarkRecordIn) -> dict:
    bench_id = store.benchmarks.record(
        store.athlete_id, body.benchmark_id, body.result_value,
        body.result_unit, body.test_date, body.detail)
    return {"status": "recorded", "id": bench_id}


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
    done = {s["session_date"]: s for s in store.sessions.last_n(store.athlete_id, 60)}
    for day in week["days"]:
        rec = done.get(day["date"])
        day["done"] = ({"discipline": rec["discipline"], "duration_min": rec["duration_min"],
                        "status": rec["status"]} if rec else None)
    return week


# ---------- Tableau de bord analytics (dérivé des données enregistrées) ----------
@app.get("/analytics/snapshot")
def analytics_snapshot() -> dict:
    return _analytics_from_store()
