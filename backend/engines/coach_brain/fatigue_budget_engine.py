from __future__ import annotations
from .models import (BudgetReport, BudgetStatus, Discipline, SessionLoad,
                     WeekType, WeeklyBudget)

# Budgets calibrated on the athlete's 3/2/2/3 police rhythm:
# BIG_WORK week (5 work days: mon/tue/fri/sat/sun): 2 full OFF days -> lower budget
# SMALL_WORK week (2 work days: wed/thu): 5 OFF days -> higher budget + swim recovery
_BUDGETS = {
    WeekType.BIG_WORK: WeeklyBudget(
        WeekType.BIG_WORK,
        total_budget_su=420.0,
        per_discipline_cap={
            Discipline.RUN.value: 180.0,
            Discipline.CROSSFIT.value: 160.0,
            Discipline.STRENGTH.value: 140.0,
            Discipline.SWIM.value: 60.0,
        },
        hard_sessions_cap=2,
    ),
    WeekType.SMALL_WORK: WeeklyBudget(
        WeekType.SMALL_WORK,
        total_budget_su=620.0,
        per_discipline_cap={
            Discipline.RUN.value: 260.0,
            Discipline.CROSSFIT.value: 240.0,
            Discipline.STRENGTH.value: 200.0,
            Discipline.SWIM.value: 90.0,
        },
        hard_sessions_cap=4,
    ),
}

_HARD_RPE = 7.0


class FatigueBudgetEngine:
    """Weekly stress-unit budget with per-discipline caps and chronic debt tracking."""

    def budget_for(self, week_type: WeekType) -> WeeklyBudget:
        return _BUDGETS[week_type]

    def report(self, week_type: WeekType, sessions: list[SessionLoad]) -> BudgetReport:
        budget = _BUDGETS[week_type]
        per_disc: dict[str, float] = {}
        consumed = 0.0
        hard = 0
        warnings: list[str] = []
        for s in sessions:
            s.validate()
            su = s.stress_units
            consumed += su
            per_disc[s.discipline.value] = round(per_disc.get(s.discipline.value, 0.0) + su, 1)
            if s.intensity >= _HARD_RPE:
                hard += 1
        pct = round(consumed / budget.total_budget_su * 100, 1)
        if pct < 60:
            status = BudgetStatus.UNDER
        elif pct < 85:
            status = BudgetStatus.ON_TRACK
        elif pct <= 100:
            status = BudgetStatus.NEAR_LIMIT
            warnings.append("approche_limite_hebdo")
        else:
            status = BudgetStatus.OVER
            warnings.append("budget_depasse_recuperation_obligatoire")
        for disc, cap in budget.per_discipline_cap.items():
            if per_disc.get(disc, 0.0) > cap:
                warnings.append(f"cap_{disc}_depasse")
        if hard > budget.hard_sessions_cap:
            warnings.append("trop_de_seances_dures")
        return BudgetReport(
            status=status, consumed_su=round(consumed, 1),
            budget_su=budget.total_budget_su,
            remaining_su=round(max(0.0, budget.total_budget_su - consumed), 1),
            consumed_pct=pct, per_discipline_su=per_disc,
            hard_sessions_done=hard, warnings=warnings,
        )

    @staticmethod
    def acwr(acute_7d_su: float, chronic_28d_avg_su: float) -> tuple[float, str]:
        """Acute:Chronic Workload Ratio. Sweet spot 0.8-1.3 (Gabbett)."""
        if chronic_28d_avg_su <= 0:
            return 0.0, "insufficient_history"
        ratio = round(acute_7d_su / chronic_28d_avg_su, 2)
        if ratio < 0.8:
            return ratio, "detraining_risk"
        if ratio <= 1.3:
            return ratio, "optimal"
        if ratio <= 1.5:
            return ratio, "elevated_injury_risk"
        return ratio, "high_injury_risk"
