from __future__ import annotations
from crossfit_models import CrossFitCategory, CrossFitFamily

_RAW = [
("strength_back_squat","Back Squat","STRENGTH",["back_squat"],["squat","strength"],60,["barbell","rack"]),
("strength_front_squat","Front Squat","STRENGTH",["front_squat"],["squat","strength"],60,["barbell","rack"]),
("strength_deadlift","Deadlift","STRENGTH",["deadlift"],["hinge","strength"],60,["barbell"]),
("strength_strict_press","Strict Press","STRENGTH",["strict_press"],["press","strength"],55,["barbell"]),
("strength_bench_press","Bench Press","STRENGTH",["bench_press"],["press","strength"],55,["barbell","bench"]),
("strength_push_press","Push Press","STRENGTH",["push_press"],["press","power"],55,["barbell"]),
("strength_rdl","Romanian Deadlift","STRENGTH",["romanian_deadlift"],["hinge","posterior_chain"],50,["barbell"]),
("strength_walking_lunge","Walking Lunge","STRENGTH",["walking_lunge"],["lunge","unilateral"],45,["dumbbell"]),
("strength_pull","Pull Strength","STRENGTH",["strict_pullup","ring_row"],["pull","strength"],45,["pullup_bar","rings"]),
("strength_builder","Strength Builder","STRENGTH",["deadlift","strict_press"],["strength","mixed"],60,["barbell"]),
("gym_pullup","Pull-Up","GYMNASTICS",["pullup"],["pull","gymnastics"],45,["pullup_bar"]),
("gym_pushup","Push-Up","GYMNASTICS",["pushup"],["push","gymnastics"],35,[]),
("gym_ring_row","Ring Row","GYMNASTICS",["ring_row"],["pull","gymnastics"],35,["rings"]),
("gym_ttb","Toes-to-Bar","GYMNASTICS",["toes_to_bar"],["core","gymnastics"],40,["pullup_bar"]),
("gym_hspu","Handstand Push-Up","GYMNASTICS",["handstand_pushup"],["press","skill"],45,["wall"]),
("gym_rope_climb","Rope Climb","GYMNASTICS",["rope_climb"],["pull","skill"],45,["rope"]),
("gym_core_builder","Core Builder","GYMNASTICS",["hollow_hold","plank"],["core","recovery"],30,[]),
("gym_skill_builder","Skill Builder","GYMNASTICS",["handstand_hold","kip_swing"],["skill","coordination"],40,["wall","pullup_bar"]),
("gym_muscleup_prep","Muscle-Up Prep","GYMNASTICS",["transition_drill","strict_pullup"],["skill","pull"],45,["rings","pullup_bar"]),
("gym_volume","Gymnastics Volume","GYMNASTICS",["pullup","pushup","situp"],["gymnastics","volume"],45,["pullup_bar"]),
("metcon_short_amrap","Short AMRAP","METCON",["row","burpee"],["engine","mixed"],20,["rower"]),
("metcon_long_amrap","Long AMRAP","METCON",["run","air_squat"],["engine","volume"],35,[]),
("metcon_short_emom","Short EMOM","METCON",["kettlebell_swing","pushup"],["interval","mixed"],20,["kettlebell"]),
("metcon_long_emom","Long EMOM","METCON",["row","wall_ball"],["interval","engine"],35,["rower","wall_ball"]),
("metcon_for_time","For Time","METCON",["burpee","box_jump"],["speed","mixed"],25,["box"]),
("metcon_chipper","Chipper","METCON",["row","burpee","situp"],["volume","mixed"],40,["rower"]),
("metcon_sprint","Sprint MetCon","METCON",["bike","burpee"],["speed","anaerobic"],18,["bike"]),
("metcon_mixed_modal","Mixed Modal","METCON",["run","pullup","kettlebell_swing"],["mixed","engine"],30,["pullup_bar","kettlebell"]),
("metcon_density","Density Builder","METCON",["wall_ball","situp"],["density","engine"],30,["wall_ball"]),
("metcon_competition","Competition MetCon","METCON",["row","thruster","pullup"],["competition","mixed"],45,["rower","barbell","pullup_bar"]),
("hyrox_skierg","SkiErg","HYROX",["ski_erg"],["erg","engine"],45,["skierg"]),
("hyrox_row","Row","HYROX",["row"],["erg","engine"],45,["rower"]),
("hyrox_farmer_carry","Farmer Carry","HYROX",["farmer_carry"],["carry","grip"],50,["dumbbell"]),
("hyrox_sled_push","Sled Push","HYROX",["sled_push"],["push","power"],55,["sled"]),
("hyrox_sled_pull","Sled Pull","HYROX",["sled_pull"],["pull","power"],55,["sled"]),
("hyrox_wall_balls","Wall Balls","HYROX",["wall_ball"],["squat","engine"],45,["wall_ball"]),
("hyrox_burpee_broad_jump","Burpee Broad Jump","HYROX",["burpee_broad_jump"],["jump","engine"],45,[]),
("hyrox_run_erg","Run + Erg","HYROX",["run","row"],["run","erg"],50,["rower"]),
("hyrox_run_carry","Run + Carry","HYROX",["run","farmer_carry"],["run","carry"],55,["dumbbell"]),
("hyrox_simulation","Hyrox Simulation","HYROX",["run","ski_erg","sled_push","wall_ball"],["competition","hyrox"],75,["skierg","sled","wall_ball"]),
("tactical_ruck","Ruck","TACTICAL",["ruck"],["loaded","endurance"],60,["ruck"]),
("tactical_sandbag_carry","Sandbag Carry","TACTICAL",["sandbag_carry"],["carry","loaded"],55,["sandbag"]),
("tactical_stair_climb","Stair Climb","TACTICAL",["stair_climb"],["climb","endurance"],50,[]),
("tactical_grip_builder","Grip Builder","TACTICAL",["farmer_carry","dead_hang"],["grip","carry"],45,["dumbbell","pullup_bar"]),
("tactical_crawl","Crawl","TACTICAL",["bear_crawl"],["crawl","core"],35,[]),
("tactical_loaded_march","Loaded March","TACTICAL",["loaded_march"],["loaded","endurance"],70,["ruck"]),
("tactical_obstacle_prep","Obstacle Prep","TACTICAL",["crawl","vault","carry"],["obstacle","mixed"],50,["sandbag"]),
("tactical_circuit","Tactical Circuit","TACTICAL",["sandbag_carry","burpee","run"],["tactical","mixed"],45,["sandbag"]),
("tactical_rescue_carry","Rescue Carry","TACTICAL",["rescue_carry"],["carry","power"],45,["sandbag"]),
("tactical_raid_hybrid","RAID Tactical Hybrid","TACTICAL",["run","ruck","sandbag_carry"],["raid","tactical"],75,["ruck","sandbag"]),
]

CROSSFIT_FAMILIES = [
    CrossFitFamily(fid, name, CrossFitCategory[cat], moves, tags, dur, eq)
    for fid, name, cat, moves, tags, dur, eq in _RAW
]

def get_families() -> list[CrossFitFamily]:
    return list(CROSSFIT_FAMILIES)

def get_family_count() -> int:
    return len(CROSSFIT_FAMILIES)
