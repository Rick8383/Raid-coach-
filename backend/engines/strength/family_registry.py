from __future__ import annotations
from .models import StrengthCategory, StrengthFamily

# fid, name, category, base_min, tags, raid_relevance
_RAW = [
    # PUSH (12)
    ("str_bench_heavy", "Bench Press Heavy", "PUSH", 50, ["bench", "max_strength"], 4),
    ("str_bench_volume", "Bench Press Volume", "PUSH", 55, ["bench", "hypertrophy"], 4),
    ("str_ohp_strict", "Strict Overhead Press", "PUSH", 45, ["ohp", "shoulders"], 3),
    ("str_pushup_endurance", "Push-Up Endurance", "PUSH", 35, ["pushup", "endurance", "raid_test"], 5),
    ("str_pushup_weighted", "Weighted Push-Up", "PUSH", 40, ["pushup", "strength"], 4),
    ("str_dips_strength", "Dips Strength", "PUSH", 40, ["dips", "raid_test"], 5),
    ("str_dips_volume", "Dips Volume", "PUSH", 40, ["dips", "endurance", "raid_test"], 5),
    ("str_incline_press", "Incline Press", "PUSH", 45, ["bench", "upper_chest"], 2),
    ("str_db_press", "Dumbbell Press Unilateral", "PUSH", 45, ["dumbbell", "stability"], 2),
    ("str_pushup_variations", "Push-Up Variations", "PUSH", 35, ["pushup", "gymnastic"], 3),
    ("str_landmine_press", "Landmine Press", "PUSH", 40, ["functional", "core"], 2),
    ("str_push_density", "Push Density Block", "PUSH", 35, ["density", "endurance"], 4),
    # PULL (14)
    ("str_pullup_strength", "Pull-Up Strength (weighted)", "PULL", 45, ["pullup", "raid_test"], 5),
    ("str_pullup_volume", "Pull-Up Volume", "PULL", 40, ["pullup", "endurance", "raid_test"], 5),
    ("str_pullup_emom", "Pull-Up EMOM", "PULL", 30, ["pullup", "density", "raid_test"], 5),
    ("str_rope_climb", "Rope Climb Technique & Power", "PULL", 40, ["rope", "raid_test", "grip"], 5),
    ("str_rope_climb_legless", "Legless Rope Climb", "PULL", 40, ["rope", "raid_test", "grip"], 5),
    ("str_deadlift_heavy", "Deadlift Heavy", "PULL", 55, ["deadlift", "max_strength"], 4),
    ("str_deadlift_volume", "Deadlift Volume", "PULL", 55, ["deadlift", "hypertrophy"], 3),
    ("str_row_barbell", "Barbell Row", "PULL", 45, ["row", "back"], 3),
    ("str_row_unilateral", "Unilateral Row", "PULL", 40, ["row", "stability"], 2),
    ("str_grip_complex", "Grip Strength Complex", "PULL", 30, ["grip", "forearm", "raid_test"], 5),
    ("str_lat_endurance", "Lat Endurance Circuit", "PULL", 35, ["pullup", "endurance"], 4),
    ("str_face_pull_health", "Shoulder Health Pull", "PULL", 25, ["prehab", "rear_delt"], 2),
    ("str_towel_pullup", "Towel/Thick Grip Pull-Up", "PULL", 35, ["grip", "pullup", "raid_test"], 5),
    ("str_pull_density", "Pull Density Block", "PULL", 35, ["density", "endurance"], 4),
    # LEGS (12)
    ("str_squat_heavy", "Back Squat Heavy", "LEGS", 55, ["squat", "max_strength"], 4),
    ("str_squat_volume", "Back Squat Volume", "LEGS", 55, ["squat", "hypertrophy"], 3),
    ("str_front_squat", "Front Squat", "LEGS", 50, ["squat", "core"], 3),
    ("str_lunge_loaded", "Loaded Walking Lunge", "LEGS", 40, ["lunge", "carry_prep"], 4),
    ("str_step_up_weighted", "Weighted Step-Up", "LEGS", 40, ["stepup", "mountain_prep"], 4),
    ("str_rdl", "Romanian Deadlift", "LEGS", 45, ["hinge", "hamstring"], 3),
    ("str_single_leg", "Single Leg Strength", "LEGS", 40, ["unilateral", "stability"], 3),
    ("str_calf_tibialis", "Calf & Tibialis Block", "LEGS", 25, ["lower_leg", "injury_prev"], 3),
    ("str_wall_sit_iso", "Isometric Leg Endurance", "LEGS", 30, ["isometric", "endurance"], 3),
    ("str_box_jump_power", "Box Jump Power", "LEGS", 35, ["plyo", "power"], 3),
    ("str_sled_push", "Sled Push/Drag", "LEGS", 35, ["sled", "conditioning"], 4),
    ("str_leg_density", "Leg Density Block", "LEGS", 40, ["density", "endurance"], 3),
    # ASSISTANCE (10)
    ("str_core_antiflexion", "Core Anti-Flexion", "ASSISTANCE", 30, ["core", "plank"], 4),
    ("str_core_raid", "RAID Core (leg raises)", "ASSISTANCE", 30, ["core", "leg_raise", "raid_test"], 5),
    ("str_core_rotation", "Core Rotation & Carry", "ASSISTANCE", 30, ["core", "rotation"], 3),
    ("str_shoulder_stability", "Shoulder Stability", "ASSISTANCE", 25, ["prehab", "shoulder"], 3),
    ("str_hip_mobility_strength", "Hip Mobility & Strength", "ASSISTANCE", 30, ["mobility", "hip"], 3),
    ("str_neck_traps", "Neck & Traps (casque/équipement)", "ASSISTANCE", 20, ["neck", "tactical"], 3),
    ("str_forearm_iso", "Forearm Isometrics", "ASSISTANCE", 20, ["grip", "forearm"], 4),
    ("str_back_extension", "Posterior Chain Assistance", "ASSISTANCE", 30, ["lower_back", "prehab"], 3),
    ("str_ankle_prep", "Ankle Resilience", "ASSISTANCE", 20, ["ankle", "injury_prev"], 3),
    ("str_full_body_prehab", "Full Body Prehab Circuit", "ASSISTANCE", 35, ["prehab", "circuit"], 3),
    # OLYMPIC (4)
    ("str_power_clean", "Power Clean", "OLYMPIC", 45, ["clean", "power"], 3),
    ("str_push_press", "Push Press", "OLYMPIC", 40, ["jerk", "power"], 3),
    ("str_hang_clean", "Hang Clean Technique", "OLYMPIC", 40, ["clean", "technique"], 2),
    ("str_db_snatch", "Dumbbell Snatch", "OLYMPIC", 35, ["snatch", "conditioning"], 3),
    # RAID_SPECIFIC (8)
    ("str_raid_circuit_test", "RAID Test Simulation Circuit", "RAID_SPECIFIC", 50,
     ["raid_test", "pullup", "pushup", "dips", "leg_raise", "rope"], 5),
    ("str_raid_max_day", "RAID Max Rep Day", "RAID_SPECIFIC", 45, ["raid_test", "max_effort"], 5),
    ("str_loaded_carry", "Loaded Carry Complex", "RAID_SPECIFIC", 40, ["carry", "farmer", "sandbag"], 5),
    ("str_sandbag_work", "Sandbag Strength", "RAID_SPECIFIC", 40, ["sandbag", "functional"], 4),
    ("str_partner_drag", "Body Drag & Evacuation", "RAID_SPECIFIC", 35, ["drag", "rescue"], 5),
    ("str_weighted_vest_circuit", "Weighted Vest Circuit", "RAID_SPECIFIC", 45, ["vest", "conditioning"], 5),
    ("str_combat_strength", "Combat Strength (grappling base)", "RAID_SPECIFIC", 40, ["combat", "grip", "core"], 4),
    ("str_climb_obstacle", "Climb & Obstacle Strength", "RAID_SPECIFIC", 40, ["climb", "obstacle", "rope"], 5),
]

STRENGTH_FAMILIES = [
    StrengthFamily(fid, name, StrengthCategory[cat], dur, tags, raid)
    for fid, name, cat, dur, tags, raid in _RAW
]


def get_strength_families() -> list[StrengthFamily]:
    return list(STRENGTH_FAMILIES)


def get_strength_family_count() -> int:
    return len(STRENGTH_FAMILIES)


def get_families_by_category(category: StrengthCategory) -> list[StrengthFamily]:
    return [f for f in STRENGTH_FAMILIES if f.category == category]


def get_raid_test_families() -> list[StrengthFamily]:
    return [f for f in STRENGTH_FAMILIES if f.raid_relevance >= 5]
