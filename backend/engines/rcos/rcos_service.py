from __future__ import annotations
from .memory_twin_life import AthleteMemory, DigitalTwin, LifeEngine
from .models import (AnnualPlan, BestActionToday, SeasonBlock, SeasonPhase)


class AnnualPlanner:
    """Rétro-planning depuis la semaine de sélection.
    Macro-structure RAID : cycles Base→Build→Peak répétés, taper final,
    benchmarks officiels à chaque fin de Build."""

    # Weekly SU targets per phase: (grande semaine police, petite semaine)
    PHASE_SU = {
        SeasonPhase.BASE: (340.0, 500.0),
        SeasonPhase.BUILD: (400.0, 590.0),
        SeasonPhase.PEAK: (420.0, 620.0),
        SeasonPhase.TAPER: (220.0, 300.0),
        SeasonPhase.SELECTION: (120.0, 120.0),
        SeasonPhase.TRANSITION: (180.0, 260.0),
    }

    def build(self, weeks_to_selection: int) -> AnnualPlan:
        if not 8 <= weeks_to_selection <= 220:
            raise ValueError("weeks_to_selection 8-220")
        blocks: list[SeasonBlock] = []
        milestones: list[str] = []
        w = 0
        # Reserve the end: taper (3) + selection (1)
        core_end = weeks_to_selection - 4
        cycle = [(SeasonPhase.BASE, 6, "Volume aérobie + gym skills (T2B, corde, volume tractions)"),
                 (SeasonPhase.BUILD, 5, "Intensité + WODs sélection + force spécifique"),
                 (SeasonPhase.PEAK, 2, "Benchmarks officiels + simulation présélection"),
                 (SeasonPhase.TRANSITION, 1, "Décharge, natation, mobilité sciatique")]
        ci = 0
        while w <= core_end:
            phase, length, focus = cycle[ci % len(cycle)]
            end = min(w + length - 1, core_end)
            blocks.append(SeasonBlock(phase, w, end, focus, self.PHASE_SU[phase]))
            if phase == SeasonPhase.PEAK:
                milestones.append(f"S{end}: re-test benchmarks officiels (WOD PDC + WOD Force)")
            w = end + 1
            ci += 1
        blocks.append(SeasonBlock(SeasonPhase.TAPER, w, w + 2,
                                  "Affûtage : fraîcheur, technique, confiance",
                                  self.PHASE_SU[SeasonPhase.TAPER]))
        blocks.append(SeasonBlock(SeasonPhase.SELECTION, w + 3, w + 3,
                                  "SEMAINE DE SÉLECTION",
                                  self.PHASE_SU[SeasonPhase.SELECTION]))
        milestones.append(f"S{w + 3}: SÉLECTION RAID")
        plan = AnnualPlan(weeks_total=weeks_to_selection,
                          selection_week=w + 3, blocks=blocks,
                          key_milestones=milestones)
        plan.validate()
        return plan

    @staticmethod
    def phase_for_week(plan: AnnualPlan, week: int) -> SeasonBlock:
        for b in plan.blocks:
            if b.week_start <= week <= b.week_end:
                return b
        return plan.blocks[-1]


class PriorityEngine:
    """Hiérarchie quotidienne : sécurité > objectif principal > maintien > secondaire."""

    @staticmethod
    def rank(form_label: str, risk_signals: list[str], weeks_to_selection: int,
             capacity: float) -> list[str]:
        if risk_signals and any("sciatique" in s.lower() for s in risk_signals):
            return ["protéger_le_dos", "récupération", "maintien_aérobie_doux"]
        if form_label == "overreached":
            return ["récupération", "sommeil", "maintien_technique"]
        if capacity < 0.4:
            return ["maintien_minimal", "mobilité", "sommeil"]
        if weeks_to_selection <= 4:
            return ["fraîcheur", "spécifique_sélection", "confiance"]
        if form_label == "fresh":
            return ["développement_prioritaire", "qualité_haute", "volume"]
        return ["développement_prioritaire", "maintien_acquis", "récupération_active"]


class RCOSService:
    """Best Action Today : la synthèse de tout le système."""

    def __init__(self) -> None:
        self.memory = AthleteMemory()
        self.twin = DigitalTwin()
        self.life = LifeEngine()
        self.planner = AnnualPlanner()

    def best_action_today(self, plan: AnnualPlan, current_week: int,
                          date: str, daily_action_hint: str) -> BestActionToday:
        """daily_action_hint : sortie du DailyDecisionEngine (B10) —
        le RCOS la contextualise avec mémoire, twin, saison et vie."""
        block = self.planner.phase_for_week(plan, current_week)
        digest = self.memory.digest()
        form = self.twin.form_label()
        capacity = self.life.capacity_for(date)
        priorities = PriorityEngine.rank(form, digest.risk_signals,
                                         plan.selection_week - current_week,
                                         capacity)
        action = daily_action_hint
        why_parts = [f"phase {block.phase.value} (focus: {block.focus})",
                     f"forme: {form} (TSB {self.twin.state.form})",
                     f"priorité: {priorities[0]}"]
        if capacity < 1.0:
            why_parts.append(f"capacité réduite à {int(capacity * 100)}% (contraintes vie)")
            action = f"{daily_action_hint} — version réduite ({int(capacity * 100)}%)"
        if priorities[0] in ("protéger_le_dos", "récupération"):
            action = "Récupération pilotée : natation douce + mobilité"
        if_one = {
            "protéger_le_dos": "20' mobilité hanche/nerf sciatique",
            "récupération": "Sieste + marche 20'",
            "fraîcheur": "10' technique corde + visualisation",
            "développement_prioritaire": "Bloc gym 25': T2B + tractions",
            "maintien_minimal": "20' Z2 facile",
            "maintien_aérobie_doux": "30' natation Z1",
        }.get(priorities[0], "30' Z2")
        return BestActionToday(
            action=action,
            why=" · ".join(why_parts),
            if_only_one_thing=if_one,
            week_context=f"Semaine {current_week}/{plan.weeks_total} — {block.phase.value}",
            season_context=f"Sélection dans {plan.selection_week - current_week} semaines",
            memory_notes=(digest.risk_signals[:2] + digest.works_well[:1]),
            form_state=form,
        )
