from __future__ import annotations
from .models import (ActivityLevel, DayType, MacroTarget, NutritionPhase,
                     NutritionProfile)

_ACTIVITY_FACTOR = {
    ActivityLevel.REST: 1.30,
    ActivityLevel.LIGHT: 1.45,
    ActivityLevel.MODERATE: 1.60,
    ActivityLevel.HIGH: 1.85,
    ActivityLevel.EXTREME: 2.10,
}

_PHASE_ADJUST = {
    NutritionPhase.RECOMP: -0.12,     # déficit modéré, protéines hautes
    NutritionPhase.BUILD: +0.08,
    NutritionPhase.MAINTAIN: 0.0,
    NutritionPhase.PEAK: -0.05,
    NutritionPhase.RACE_WEEK: +0.05,  # surcompensation glucidique
    NutritionPhase.RECOVERY: 0.0,
}

# protein g/kg per phase (high end for recomp to preserve muscle in deficit)
_PROTEIN_G_KG = {
    NutritionPhase.RECOMP: 2.2,
    NutritionPhase.BUILD: 1.9,
    NutritionPhase.MAINTAIN: 1.8,
    NutritionPhase.PEAK: 2.0,
    NutritionPhase.RACE_WEEK: 1.6,
    NutritionPhase.RECOVERY: 2.0,
}


class CaloricNeedsEngine:
    @staticmethod
    def bmr_mifflin(profile: NutritionProfile) -> int:
        profile.validate()
        s = 5 if profile.sex == "m" else -161
        return round(10 * profile.weight_kg + 6.25 * profile.height_cm
                     - 5 * profile.age + s)

    @staticmethod
    def bmr_katch_mcardle(profile: NutritionProfile) -> int | None:
        """More accurate when body fat % is known."""
        if profile.body_fat_pct is None:
            return None
        lbm = profile.weight_kg * (1 - profile.body_fat_pct / 100)
        return round(370 + 21.6 * lbm)

    def tdee(self, profile: NutritionProfile, activity: ActivityLevel) -> int:
        bmr = self.bmr_katch_mcardle(profile) or self.bmr_mifflin(profile)
        return round(bmr * _ACTIVITY_FACTOR[activity])

    def target_calories(self, profile: NutritionProfile, activity: ActivityLevel) -> int:
        base = self.tdee(profile, activity)
        adjusted = round(base * (1 + _PHASE_ADJUST[profile.phase]))
        # Floor: never below BMR * 1.15 (safety)
        floor = round(self.bmr_mifflin(profile) * 1.15)
        # Clamp aux bornes de MacroTarget.validate : les profils extrêmes
        # (très léger sédentaire / très lourd en build) doivent produire une
        # cible utilisable, pas une erreur 422
        return min(max(adjusted, floor, 1200), 6000)


class MacroEngine:
    """Carb cycling: HIGH on double-session days, LOW on rest days."""

    _CARB_G_KG = {DayType.HIGH: 6.0, DayType.MEDIUM: 4.0, DayType.LOW: 2.5}

    def __init__(self) -> None:
        self.calories_engine = CaloricNeedsEngine()

    @staticmethod
    def day_type_for(activity: ActivityLevel) -> DayType:
        if activity in (ActivityLevel.HIGH, ActivityLevel.EXTREME):
            return DayType.HIGH
        if activity in (ActivityLevel.MODERATE, ActivityLevel.LIGHT):
            return DayType.MEDIUM
        return DayType.LOW

    def compute(self, profile: NutritionProfile, activity: ActivityLevel) -> MacroTarget:
        profile.validate()
        calories = self.calories_engine.target_calories(profile, activity)
        day_type = self.day_type_for(activity)

        protein_g = round(_PROTEIN_G_KG[profile.phase] * profile.weight_kg)
        carbs_g = round(self._CARB_G_KG[day_type] * profile.weight_kg)
        # carbs capped so that fat never < 0.6 g/kg (hormonal floor)
        fat_floor_g = round(0.6 * profile.weight_kg)
        remaining = calories - protein_g * 4 - fat_floor_g * 9
        carbs_g = min(carbs_g, max(0, round(remaining / 4)))
        fat_g = max(fat_floor_g, round((calories - protein_g * 4 - carbs_g * 4) / 9))

        water = round(0.035 * profile.weight_kg
                      + (0.5 if day_type == DayType.MEDIUM else 1.0 if day_type == DayType.HIGH else 0.0), 1)
        notes = []
        if profile.phase == NutritionPhase.RECOMP:
            notes.append("Déficit modéré ~12% : perte de gras lente, muscle préservé (protéines 2,2 g/kg)")
            notes.append("Placer les glucides autour des séances (avant/après)")
        if day_type == DayType.HIGH:
            notes.append("Jour double séance : collation glucidique entre les deux séances")
        target = MacroTarget(day_type, calories, protein_g, carbs_g, fat_g, water, notes)
        target.validate()
        return target
