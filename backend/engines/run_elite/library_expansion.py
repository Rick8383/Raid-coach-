from __future__ import annotations

from engines.legacy.running_models import RunningFamily, RunningFamilyType

# Expansion: existing 25 families (consolidation repo) + 85 new = 110 total.
# Categories Elite+: Recovery, Z2/Base, Fartlek, Tempo, Threshold, VMA Short,
# VMA Long, Hills, Long Run, Specific, Test.

_NEW_RAW = [
    # RECOVERY (5 new)
    ("run_recovery_short", "Short Recovery 20'", "RECOVERY", 20, ["road"], ["recovery"]),
    ("run_recovery_soft", "Soft Surface Recovery", "RECOVERY", 35, ["trail"], ["recovery", "soft"]),
    ("run_recovery_walkrun", "Walk-Run Recovery", "RECOVERY", 35, ["road"], ["recovery", "walk_run"]),
    ("run_recovery_strides", "Recovery + Strides", "RECOVERY", 35, ["road"], ["recovery", "strides"]),
    # Z2 / BASE (9 new)
    ("run_z2_45", "Z2 Base 45'", "EASY", 45, ["road"], ["z2", "aerobic"]),
    ("run_z2_60", "Z2 Base 60'", "EASY", 60, ["road"], ["z2", "aerobic"]),
    ("run_z2_75", "Z2 Base 75'", "EASY", 75, ["road"], ["z2", "aerobic"]),
    ("run_z2_trail", "Z2 Trail", "EASY", 60, ["trail"], ["z2", "technical_light"]),
    ("run_z2_hilly", "Z2 Hilly", "EASY", 60, ["hilly"], ["z2", "elevation"]),
    ("run_z2_strides", "Z2 + 6 lignes droites", "EASY", 55, ["road"], ["z2", "strides"]),
    ("run_z2_hr_capped", "Z2 FC plafonnée stricte", "EASY", 60, ["road"], ["z2", "hr_discipline"]),
    # FARTLEK (8 new)
    ("run_fartlek_pyramid", "Fartlek Pyramide 1-2-3-2-1", "INTERVAL", 50, ["road"], ["fartlek", "pyramid"]),
    ("run_fartlek_30_30", "Fartlek 30/30 libre", "INTERVAL", 45, ["road"], ["fartlek", "30_30"]),
    ("run_fartlek_trail", "Fartlek Trail aux sensations", "INTERVAL", 55, ["trail"], ["fartlek", "feel"]),
    ("run_fartlek_kenyan", "Fartlek Kényan", "INTERVAL", 50, ["road"], ["fartlek", "continuous"]),
    ("run_fartlek_hills", "Fartlek Côtes naturelles", "INTERVAL", 50, ["hilly"], ["fartlek", "hills"]),
    ("run_fartlek_mins", "Fartlek minutes 5-4-3-2-1", "INTERVAL", 50, ["road"], ["fartlek", "ladder"]),
    ("run_fartlek_raid", "Fartlek RAID terrain varié", "INTERVAL", 55, ["mixed"], ["fartlek", "raid"]),
    # TEMPO (8 new)
    ("run_tempo_20", "Tempo 20' continu", "TEMPO", 45, ["road"], ["tempo", "steady"]),
    ("run_tempo_2x15", "Tempo 2×15'", "TEMPO", 55, ["road"], ["tempo", "blocks"]),
    ("run_tempo_3x10", "Tempo 3×10'", "TEMPO", 55, ["road"], ["tempo", "blocks"]),
    ("run_tempo_progressif", "Tempo progressif 30'", "TEMPO", 55, ["road"], ["tempo", "progressive"]),
    ("run_tempo_trail", "Tempo Trail", "TEMPO", 55, ["trail"], ["tempo", "technical"]),
    ("run_tempo_hilly", "Tempo vallonné", "TEMPO", 55, ["hilly"], ["tempo", "elevation"]),
    ("run_tempo_finish", "SL + finish tempo 15'", "TEMPO", 75, ["road"], ["tempo", "combo"]),
    # THRESHOLD (8 new)
    ("run_threshold_4x8", "Seuil 4×8' r2'", "THRESHOLD", 60, ["road"], ["threshold", "classic"]),
    ("run_threshold_3x12", "Seuil 3×12' r2'30", "THRESHOLD", 65, ["road"], ["threshold", "long"]),
    ("run_threshold_2x20", "Seuil 2×20' r3'", "THRESHOLD", 65, ["road"], ["threshold", "long"]),
    ("run_threshold_5x6", "Seuil 5×6' r90s", "THRESHOLD", 55, ["road"], ["threshold", "short"]),
    ("run_threshold_alternance", "Seuil alterné (1' vite/1' seuil)", "THRESHOLD", 55, ["road"], ["threshold", "mixed"]),
    ("run_threshold_trail", "Seuil Trail", "THRESHOLD", 60, ["trail"], ["threshold", "technical"]),
    ("run_threshold_cv", "Critical Velocity 6×4'", "THRESHOLD", 55, ["track"], ["threshold", "cv"]),
    ("run_threshold_cooper_pace", "Blocs allure Cooper", "THRESHOLD", 50, ["track"], ["threshold", "cooper_specific"]),
    # VMA SHORT (9 new)
    ("run_vma_30_30", "VMA 2×(10×30/30)", "INTERVAL", 45, ["track"], ["vma_short", "30_30"]),
    ("run_vma_200", "VMA 12×200 m", "INTERVAL", 45, ["track"], ["vma_short", "200"]),
    ("run_vma_300", "VMA 10×300 m", "INTERVAL", 50, ["track"], ["vma_short", "300"]),
    ("run_vma_400", "VMA 8×400 m", "INTERVAL", 50, ["track"], ["vma_short", "400"]),
    ("run_vma_hill_sprints", "VMA côtes courtes 10×30s", "HILL", 45, ["hill"], ["vma_short", "hill"]),
    ("run_vma_15_15", "VMA 2×(12×15/15)", "INTERVAL", 40, ["track"], ["vma_short", "15_15"]),
    ("run_vma_flying", "Sprints lancés 8×80 m", "INTERVAL", 40, ["track"], ["vma_short", "speed", "sprint_50m"]),
    ("run_vma_cooper_sim", "Simulation Cooper 12'", "INTERVAL", 40, ["track"], ["vma_short", "test_sim", "raid_test"]),
    # VMA LONG (7 new)
    ("run_vma_600", "VMA 6×600 m", "INTERVAL", 55, ["track"], ["vma_long", "600"]),
    ("run_vma_800", "VMA 6×800 m", "INTERVAL", 60, ["track"], ["vma_long", "800"]),
    ("run_vma_1000", "VMA 5×1000 m", "INTERVAL", 60, ["track"], ["vma_long", "1000"]),
    ("run_vma_1200", "VMA 4×1200 m", "INTERVAL", 60, ["road"], ["vma_long", "1200"]),
    ("run_vma_pyramid_long", "VMA pyramide 400-800-1200-800-400", "INTERVAL", 60, ["track"], ["vma_long", "pyramid"]),
    ("run_vma_3x2000", "VMA 3×2000 m", "INTERVAL", 65, ["road"], ["vma_long", "2000"]),
    ("run_vma_billat", "30/30 Billat long 3 séries", "INTERVAL", 50, ["track"], ["vma_long", "billat"]),
    # HILLS (8 new)
    ("run_hill_long_repeats", "Côtes longues 6×3'", "HILL", 60, ["hill"], ["hills", "long"]),
    ("run_hill_short_power", "Côtes courtes puissance 12×20s", "HILL", 45, ["hill"], ["hills", "power"]),
    ("run_hill_bounding", "Montées bondissantes", "HILL", 40, ["hill"], ["hills", "plyo"]),
    ("run_hill_circuit", "Circuit côte (montée dure/descente facile)", "HILL", 55, ["hill"], ["hills", "circuit"]),
    ("run_hill_downhill_skill", "Descente technique contrôlée", "HILL", 45, ["trail", "downhill"], ["hills", "descent"]),
    ("run_hill_mountain_hike", "Marche pente forte (rando-course)", "HILL", 75, ["mountain"], ["hills", "hike", "raid"]),
    ("run_hill_stairs", "Escaliers/step répétés", "HILL", 40, ["stairs"], ["hills", "stairs"]),
    # LONG RUN (8 new)
    ("run_long_2h", "Sortie longue 2h Z2", "LONG_RUN", 120, ["road"], ["long_run", "volume"]),
    ("run_long_progressive", "SL progressive (Z2→Z3 final)", "LONG_RUN", 100, ["road"], ["long_run", "progressive"]),
    ("run_long_trail_dplus", "SL Trail D+ 600-1000 m", "LONG_RUN", 130, ["trail", "mountain"], ["long_run", "elevation"]),
    ("run_long_back_to_back", "Week-end choc J2", "LONG_RUN", 90, ["trail"], ["long_run", "fatigue_resistance"]),
    ("run_long_tempo_insert", "SL avec 3×8' tempo insérés", "LONG_RUN", 105, ["road"], ["long_run", "quality"]),
    ("run_long_loaded", "SL sac lesté 5-8 kg", "LONG_RUN", 100, ["trail"], ["long_run", "loaded", "raid"]),
    ("run_long_night", "SL nocturne frontale", "LONG_RUN", 95, ["trail"], ["long_run", "night", "raid"]),
    # SPECIFIC RAID (13 new)
    ("run_raid_ruck_march", "Marche commando lestée 10-15 kg", "RAID", 80, ["mixed"], ["raid", "ruck"]),
    ("run_raid_run_carry_mix", "Alternance course/portage", "RAID", 60, ["mixed"], ["raid", "carry"]),
    ("run_raid_sandbag_run", "Course sac de sable 2×10'", "RAID", 50, ["mixed"], ["raid", "sandbag"]),
    ("run_raid_obstacle_sim", "Simulation parcours obstacles", "RAID", 55, ["mixed"], ["raid", "obstacle"]),
    ("run_raid_buddy_carry", "Portage équipier/mannequin", "RAID", 45, ["mixed"], ["raid", "rescue"]),
    ("run_raid_stairs_loaded", "Escaliers lestés", "RAID", 45, ["stairs"], ["raid", "loaded"]),
    ("run_raid_brick_swim", "Brick course + natation", "RAID", 70, ["mixed", "pool"], ["raid", "swim_combo"]),
    ("run_raid_interval_loaded", "Intervalles gilet lesté 6×3'", "RAID", 50, ["road"], ["raid", "vest"]),
    ("run_raid_terrain_mixte", "Sortie terrain mixte imprévisible", "RAID", 70, ["mixed"], ["raid", "adaptability"]),
    ("run_raid_heat_cold", "Sortie conditions difficiles", "RAID", 60, ["mixed"], ["raid", "environment"]),
    ("run_raid_sprint_repeat", "Sprints répétés 50 m (test)", "INTERVAL", 40, ["track"], ["raid", "sprint_50m", "raid_test"]),
    ("run_raid_combat_circuit", "Circuit course + combat sol", "RAID", 50, ["mixed"], ["raid", "combat"]),
    ("run_raid_full_sim", "Simulation journée présélection", "RAID", 90, ["mixed"], ["raid", "full_sim", "raid_test"]),
    # TEST (10 new)
    ("run_test_cooper", "Test Cooper 12'", "INTERVAL", 35, ["track"], ["test", "cooper", "raid_test"]),
    ("run_test_vma_demi_cooper", "Demi-Cooper 6'", "INTERVAL", 30, ["track"], ["test", "vma"]),
    ("run_test_vameval", "VAMEVAL", "INTERVAL", 35, ["track"], ["test", "vma"]),
    ("run_test_5k", "Test 5 km chrono", "INTERVAL", 40, ["road"], ["test", "5k"]),
    ("run_test_10k", "Test 10 km chrono", "INTERVAL", 60, ["road"], ["test", "10k"]),
    ("run_test_30_15", "30-15 IFT", "INTERVAL", 35, ["track"], ["test", "intermittent"]),
    ("run_test_sprint_50", "Test sprint 50 m", "INTERVAL", 25, ["track"], ["test", "sprint_50m", "raid_test"]),
    ("run_test_lactate_field", "Test seuil terrain 2×20'", "THRESHOLD", 60, ["road"], ["test", "threshold"]),
    ("run_test_hill_3min", "Test côte 3'", "HILL", 30, ["hill"], ["test", "hill_power"]),
    ("run_test_loaded_march", "Test marche lestée 8 km", "RAID", 75, ["mixed"], ["test", "ruck", "raid_test"]),
]

NEW_RUNNING_FAMILIES = [
    RunningFamily(fid, name, RunningFamilyType[typ], dur, terrain, tags)
    for fid, name, typ, dur, terrain, tags in _NEW_RAW
]


def get_extended_running_families() -> list[RunningFamily]:
    from running_family_registry import RUNNING_FAMILIES
    return list(RUNNING_FAMILIES) + list(NEW_RUNNING_FAMILIES)


def get_extended_family_count() -> int:
    return len(get_extended_running_families())
