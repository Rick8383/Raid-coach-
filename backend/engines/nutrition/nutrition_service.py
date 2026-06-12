from __future__ import annotations
from .models import (ActivityLevel, NutritionPhase, NutritionProfile,
                     RaceDayPlan, SupplementAdvice)
from .macro_engine import MacroEngine


class RaceNutritionPlanner:
    """Day-of-selection / competition nutrition. Built for RAID selection days:
    long days, repeated max-effort tests, possible swimming."""

    def selection_day_plan(self, weight_kg: float) -> RaceDayPlan:
        if not 40 <= weight_kg <= 180:
            raise ValueError("weight out of bounds")
        carb_load = round(8 * weight_kg)
        during_carb = "30-60 g de glucides/heure (boisson + barres/gels selon tolérance)"
        return RaceDayPlan(
            day_minus_1=[
                f"Charge glucidique : ~{carb_load} g de glucides répartis sur la journée",
                "Réduire les fibres et les graisses au dîner (confort digestif)",
                "Hydratation : urines claires en fin de journée",
                "Pas d'aliment nouveau, pas d'alcool, coucher tôt",
            ],
            morning=[
                "Petit-déjeuner 2h30-3h avant : 2-3 g/kg de glucides, pauvre en fibres/graisses",
                "Exemple : riz/flocons + miel + banane + œufs ou jambon, café si habituel",
                "300-500 ml d'eau au réveil + 300 ml 1h avant",
                "Éviter de tester la caféine en dose inhabituelle le jour J",
            ],
            during=[
                during_carb,
                "Entre les épreuves : petites prises (banane, pâte de fruits, boisson iso)",
                "Ne jamais rester à jeun plus de 2h sur une journée de tests",
                "Si natation : prise glucidique 30' avant, pas juste avant (confort)",
            ],
            after=[
                "Dans les 30-60 min : 1-1,2 g/kg glucides + 25-35 g protéines",
                "Repas complet dans les 2-3h",
                "Réhydratation : 1,5× le poids perdu en eau (peser avant/après si possible)",
            ],
            hydration=[
                "Objectif journée : 500-750 ml/heure d'activité, ajusté chaleur",
                "Ajouter électrolytes (sodium 500-700 mg/L) si journée longue ou chaude",
            ],
        )


class SupplementEngine:
    """Evidence-based only. No gray-area products: athlete is police, future
    RAID candidate — everything must be clean and standard."""

    def recommend(self, phase: NutritionPhase, sciatic_issue: bool = False) -> list[SupplementAdvice]:
        base = [
            SupplementAdvice("Créatine monohydrate", "3-5 g/jour", "Tous les jours, peu importe l'heure",
                             "forte", "Force, puissance répétée, récupération. Le supplément le plus étudié."),
            SupplementAdvice("Caféine", "3-4 mg/kg (~250 mg)", "45-60 min avant séances clés / tests",
                             "forte", "Endurance, perception d'effort. À tester à l'entraînement d'abord."),
            SupplementAdvice("Whey ou protéine", "20-40 g", "Post-séance ou pour atteindre le quota quotidien",
                             "forte", "Atteindre 2,2 g/kg en recomp sans excès calorique."),
            SupplementAdvice("Vitamine D3", "1000-2000 UI/jour", "Matin avec un repas gras",
                             "modérée", "Immunité, os, fonction musculaire. Surtout octobre→avril."),
            SupplementAdvice("Oméga-3 (EPA/DHA)", "2-3 g/jour", "Avec les repas",
                             "modérée", "Récupération, inflammation, santé articulaire."),
        ]
        if phase in (NutritionPhase.PEAK, NutritionPhase.RACE_WEEK):
            base.append(SupplementAdvice(
                "Bêta-alanine", "3,2-6,4 g/jour (doses fractionnées)", "Cure de 8-12 semaines avant le pic",
                "modérée", "Capacité tampon sur efforts 1-4 min (Cooper, circuits max reps)."))
        if sciatic_issue:
            base.append(SupplementAdvice(
                "Magnésium bisglycinate", "300 mg/jour", "Le soir",
                "modérée", "Détente neuromusculaire, sommeil. Pertinent avec la gêne sciatique."))
        return base


class NutritionService:
    """Build 11 orchestrator."""

    def __init__(self) -> None:
        self.macros = MacroEngine()
        self.race = RaceNutritionPlanner()
        self.supplements = SupplementEngine()

    def daily(self, profile: NutritionProfile, activity: ActivityLevel):
        return self.macros.compute(profile, activity)

    def week(self, profile: NutritionProfile,
             activities: list[ActivityLevel]):
        if len(activities) != 7:
            raise ValueError("expected 7 activity levels")
        return [self.macros.compute(profile, a) for a in activities]
