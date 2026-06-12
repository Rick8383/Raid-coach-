from __future__ import annotations
from .models import DailyContext, DailyDecision, Discipline, WeekType

_LEG_HEAVY = {Discipline.RUN.value, Discipline.CROSSFIT.value}


class DailyDecisionEngine:
    """Best action today. Hierarchy:
    1. Safety (pain / sciatic / critical recovery)
    2. Budget guardrails
    3. Schedule fit (police 3/2/2/3: double session on OFF days)
    4. Variety / pattern rotation
    Never generates a dangerous session."""

    def decide(self, ctx: DailyContext) -> DailyDecision:
        ctx.validate()
        safety: list[str] = []

        # 1 — SAFETY OVERRIDES
        if ctx.sciatic_flare:
            safety += ["sciatique_L5S1_active", "interdits: deadlift, squat lourd, flexion lombaire chargée, course descente"]
            d = DailyDecision(Discipline.SWIM, None, 30, 3.0,
                              "Poussée sciatique : décharge complète, natation douce + mobilité hanche/nerf",
                              ["marche 30'", "mobilité McKenzie", "repos total si douleur en natation"],
                              safety)
            d.validate()
            return d
        if ctx.pain_flag:
            d = DailyDecision(Discipline.RECOVERY, None, 30, 3.0,
                              "Douleur signalée : séance technique légère ou repos",
                              ["mobilité 20'", "repos total"], ["surveiller_douleur_48h"])
            d.validate()
            return d
        if ctx.readiness < 30 or ctx.sleep_quality < 25 or ctx.fatigue > 88:
            d = DailyDecision(Discipline.REST, None, 0, 1.0,
                              "Récupération critique : repos obligatoire (readiness/sommeil effondrés)",
                              ["sieste", "marche 20' max", "hydratation + nutrition"],
                              ["pas_de_negociation_sur_le_repos"])
            d.validate()
            return d

        # 2 — BUDGET GUARDRAILS
        if ctx.budget_consumed_pct >= 100:
            d = DailyDecision(Discipline.RECOVERY, None, 35, 4.0,
                              "Budget fatigue hebdo consommé : récupération active uniquement",
                              ["natation Z1 30'", "vélo très facile", "mobilité"],
                              ["budget_hebdo_atteint"])
            d.validate()
            return d
        if ctx.days_since_rest >= 6:
            d = DailyDecision(Discipline.REST, None, 0, 1.0,
                              "6+ jours consécutifs sans repos : jour off planifié",
                              ["repos complet", "natation 20' Z1 si besoin de bouger"],
                              [])
            d.validate()
            return d

        # 3 — SCHEDULE FIT (3/2/2/3)
        cap = self._intensity_cap(ctx)
        if ctx.is_work_day:
            # Work day: one shorter session, intensity capped
            action = self._pick_discipline(ctx, work_day=True)
            dur = 45 if ctx.week_type == WeekType.BIG_WORK else 55
            d = DailyDecision(action, None, dur, min(cap, 7.0),
                              f"Jour travaillé ({ctx.week_type.value}) : séance unique courte, "
                              f"qualité ciblée, intensité plafonnée",
                              ["reporter sur jour OFF si fatigue service",
                               "gym skills 30' (T2B/corde) si temps réduit"],
                              [])
            d.validate()
            return d
        # OFF day: double session possible
        primary = self._pick_discipline(ctx, work_day=False)
        secondary = self._secondary_for(primary, ctx)
        dur = 75 if ctx.readiness >= 70 else 55
        sunday_small = ctx.day_of_week == "sun" and ctx.week_type == WeekType.SMALL_WORK
        if sunday_small:
            d = DailyDecision(Discipline.SWIM, None, 40, 4.0,
                              "Dimanche petite semaine : natation récup (protocole établi) + travail apnée léger",
                              ["25m apnée × 4 en fin de séance", "mobilité 15'"],
                              [])
            d.validate()
            return d
        d = DailyDecision(primary, secondary, dur, cap,
                          "Jour OFF : double séance — run le matin, force/WOD le soir "
                          "(schéma utilisateur), volume selon readiness",
                          ["inverser matin/soir selon météo",
                           "fusionner en 1 séance CrossFit complète si temps limité"],
                          ["sciatique: échauffement lombaire systématique avant charge"])
        d.validate()
        return d

    @staticmethod
    def _intensity_cap(ctx: DailyContext) -> float:
        if ctx.readiness >= 80 and ctx.fatigue <= 40:
            return 9.5
        if ctx.readiness >= 60 and ctx.fatigue <= 60:
            return 8.0
        if ctx.readiness >= 45:
            return 6.5
        return 5.0

    @staticmethod
    def _pick_discipline(ctx: DailyContext, work_day: bool) -> Discipline:
        recent = set(ctx.last_two_disciplines)
        # Avoid 3 consecutive leg-heavy days
        if _LEG_HEAVY.issuperset(recent) and len(ctx.last_two_disciplines) >= 2:
            return Discipline.STRENGTH if Discipline.STRENGTH.value not in recent else Discipline.SWIM
        order = ([Discipline.STRENGTH, Discipline.RUN, Discipline.CROSSFIT]
                 if work_day else
                 [Discipline.RUN, Discipline.CROSSFIT, Discipline.STRENGTH])
        for d in order:
            if d.value not in recent:
                return d
        return order[0]

    @staticmethod
    def _secondary_for(primary: Discipline, ctx: DailyContext) -> Discipline | None:
        if ctx.readiness < 55:
            return None
        if primary == Discipline.RUN:
            return Discipline.STRENGTH
        if primary == Discipline.STRENGTH:
            return Discipline.CROSSFIT
        return None
