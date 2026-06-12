from __future__ import annotations
from .family_registry import STRENGTH_FAMILIES
from .models import (LEVELS, MethodType, ProgressionPhase, StrengthBlock,
                     StrengthCategory, StrengthFamily, StrengthTemplate)

_LEVEL_PARAMS = {
    # level: (sets_factor, intensity_pct, rest_sec, load_factor, duration_factor)
    "beginner": (0.7, 65.0, 120, 0.65, 0.85),
    "intermediate": (1.0, 72.5, 120, 1.0, 1.0),
    "advanced": (1.2, 80.0, 150, 1.25, 1.1),
    "deload": (0.5, 60.0, 120, 0.45, 0.7),
    "peaking": (1.0, 88.0, 210, 1.15, 1.05),
    "elite": (1.35, 85.0, 180, 1.45, 1.15),
}

_PHASE_AFFINITY = {
    "beginner": [ProgressionPhase.ACCUMULATION],
    "intermediate": [ProgressionPhase.ACCUMULATION, ProgressionPhase.INTENSIFICATION],
    "advanced": [ProgressionPhase.INTENSIFICATION],
    "deload": [ProgressionPhase.DELOAD],
    "peaking": [ProgressionPhase.PEAKING, ProgressionPhase.TEST],
    "elite": [ProgressionPhase.INTENSIFICATION, ProgressionPhase.PEAKING],
}


def _blocks_for(family: StrengthFamily, level: str) -> list[StrengthBlock]:
    sets_f, intensity, rest, _, _ = _LEVEL_PARAMS[level]
    cat = family.category

    if "raid_test" in family.pattern_tags and cat != StrengthCategory.ASSISTANCE:
        main_sets = max(3, round(4 * sets_f))
        method = MethodType.EMOM if "density" in family.pattern_tags or "EMOM" in family.name else MethodType.STANDARD
        return [
            StrengthBlock(family.family_id + "_main", main_sets, "AMRAP-2" if level != "peaking" else "max",
                          None, rest, method, "Arrêt à 2 reps de l'échec sauf jour de test"),
            StrengthBlock(family.family_id + "_back", max(2, round(2 * sets_f)), "8-12",
                          None, 90, MethodType.STANDARD, "Back-off volume"),
        ]
    if cat in (StrengthCategory.PUSH, StrengthCategory.PULL, StrengthCategory.LEGS):
        if "max_strength" in family.pattern_tags or level in ("peaking", "advanced"):
            return [
                StrengthBlock(family.family_id + "_main", max(3, round(5 * sets_f)), "3-5",
                              intensity + 5, rest + 30, MethodType.STANDARD),
                StrengthBlock(family.family_id + "_back", 3, "6-8", intensity - 10, rest,
                              MethodType.STANDARD, "Back-off"),
            ]
        return [
            StrengthBlock(family.family_id + "_main", max(3, round(4 * sets_f)), "6-10",
                          intensity, rest, MethodType.STANDARD),
            StrengthBlock(family.family_id + "_acc", 3, "10-15", intensity - 15, 90,
                          MethodType.MYO_REPS if level == "elite" else MethodType.STANDARD),
        ]
    if cat == StrengthCategory.OLYMPIC:
        return [
            StrengthBlock(family.family_id + "_tech", 4, "3", intensity - 10, rest, MethodType.STANDARD, "Technique"),
            StrengthBlock(family.family_id + "_power", max(3, round(4 * sets_f)), "2-3",
                          intensity, rest + 30, MethodType.DYNAMIC_EFFORT),
        ]
    if cat == StrengthCategory.RAID_SPECIFIC:
        return [
            StrengthBlock(family.family_id + "_circ", max(3, round(4 * sets_f)), "AMRAP-2",
                          None, rest, MethodType.DENSITY, "Circuit RAID"),
            StrengthBlock(family.family_id + "_fin", 2, "max", None, 120, MethodType.REST_PAUSE, "Finisher"),
        ]
    # ASSISTANCE
    return [
        StrengthBlock(family.family_id + "_a", max(2, round(3 * sets_f)), "10-15", None, 60, MethodType.STANDARD),
        StrengthBlock(family.family_id + "_b", max(2, round(3 * sets_f)), "12-20", None, 60, MethodType.STANDARD),
    ]


def build_strength_templates() -> list[StrengthTemplate]:
    templates: list[StrengthTemplate] = []
    for family in STRENGTH_FAMILIES:
        for level in LEVELS:
            _, _, _, load_f, dur_f = _LEVEL_PARAMS[level]
            duration = max(20, round(family.base_duration_min * dur_f))
            expected_load = round(family.base_duration_min * load_f * (1 + family.raid_relevance * 0.05), 1)
            templates.append(StrengthTemplate(
                template_id=f"{family.family_id}__{level}",
                family_id=family.family_id,
                level=level,
                duration_min=duration,
                expected_load=expected_load,
                blocks=_blocks_for(family, level),
                phase_affinity=_PHASE_AFFINITY[level],
                tags=list(family.pattern_tags),
            ))
    return templates


STRENGTH_TEMPLATES = build_strength_templates()


def get_strength_template_count() -> int:
    return len(STRENGTH_TEMPLATES)


def get_templates_for_family(family_id: str) -> list[StrengthTemplate]:
    return [t for t in STRENGTH_TEMPLATES if t.family_id == family_id]
