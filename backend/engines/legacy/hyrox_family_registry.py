from __future__ import annotations
from hyrox_models import HyroxFamily, HyroxStation

HYROX_FAMILIES = [
    HyroxFamily("hyrox_skierg", "SkiErg", [HyroxStation.RUN, HyroxStation.SKIERG], 45, ["skierg"], ["erg", "engine"]),
    HyroxFamily("hyrox_sled_push", "Sled Push", [HyroxStation.RUN, HyroxStation.SLED_PUSH], 55, ["sled"], ["push", "power"]),
    HyroxFamily("hyrox_sled_pull", "Sled Pull", [HyroxStation.RUN, HyroxStation.SLED_PULL], 55, ["sled"], ["pull", "power"]),
    HyroxFamily("hyrox_burpee_broad_jump", "Burpee Broad Jump", [HyroxStation.RUN, HyroxStation.BURPEE_BROAD_JUMP], 45, [], ["jump", "engine"]),
    HyroxFamily("hyrox_row", "Row", [HyroxStation.RUN, HyroxStation.ROW], 45, ["rower"], ["erg", "engine"]),
    HyroxFamily("hyrox_farmer_carry", "Farmer Carry", [HyroxStation.RUN, HyroxStation.FARMER_CARRY], 50, ["dumbbell"], ["carry", "grip"]),
    HyroxFamily("hyrox_sandbag_lunge", "Sandbag Lunge", [HyroxStation.RUN, HyroxStation.SANDBAG_LUNGE], 50, ["sandbag"], ["lunge", "loaded"]),
    HyroxFamily("hyrox_wall_ball", "Wall Balls", [HyroxStation.RUN, HyroxStation.WALL_BALL], 45, ["wall_ball"], ["squat", "engine"]),
    HyroxFamily("hyrox_mixed_half", "Hyrox Half Simulation", [HyroxStation.RUN, HyroxStation.SKIERG, HyroxStation.ROW, HyroxStation.FARMER_CARRY], 65, ["skierg", "rower", "dumbbell"], ["hyrox", "simulation"]),
    HyroxFamily("hyrox_full_simulation", "Hyrox Full Simulation", [HyroxStation.RUN, HyroxStation.SKIERG, HyroxStation.SLED_PUSH, HyroxStation.SLED_PULL, HyroxStation.BURPEE_BROAD_JUMP, HyroxStation.ROW, HyroxStation.FARMER_CARRY, HyroxStation.SANDBAG_LUNGE, HyroxStation.WALL_BALL], 90, ["skierg", "sled", "rower", "dumbbell", "sandbag", "wall_ball"], ["hyrox", "competition"]),
]

def get_hyrox_families() -> list[HyroxFamily]:
    return list(HYROX_FAMILIES)

def get_hyrox_family_count() -> int:
    return len(HYROX_FAMILIES)
