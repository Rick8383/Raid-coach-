from __future__ import annotations
from running_models import RunningFamily, RunningFamilyType

_RUNNING_RAW = [
("run_easy_flat","Easy Flat Run","EASY",40,["road","flat"],["aerobic","recovery"]),
("run_easy_trail","Easy Trail Run","EASY",45,["trail"],["aerobic","technical_light"]),
("run_recovery","Recovery Jog","RECOVERY",30,["road","flat"],["recovery","low_load"]),
("run_endurance_basic","Endurance Basic","ENDURANCE",60,["road"],["aerobic","volume"]),
("run_endurance_progressive","Progressive Endurance","ENDURANCE",65,["road"],["aerobic","progressive"]),
("run_long_flat","Long Flat Run","LONG_RUN",90,["road","flat"],["long_run","volume"]),
("run_long_trail","Long Trail Run","LONG_RUN",105,["trail"],["long_run","technical"]),
("run_tempo_continuous","Continuous Tempo","TEMPO",50,["road"],["tempo","steady"]),
("run_tempo_blocks","Tempo Blocks","TEMPO",55,["road"],["tempo","interval"]),
("run_threshold_cruise","Cruise Threshold","THRESHOLD",55,["road"],["threshold","controlled"]),
("run_threshold_ladder","Threshold Ladder","THRESHOLD",60,["road"],["threshold","ladder"]),
("run_interval_short","Short Intervals","INTERVAL",45,["track","road"],["speed","vo2"]),
("run_interval_medium","Medium Intervals","INTERVAL",55,["track","road"],["vo2","repeat"]),
("run_interval_long","Long Intervals","INTERVAL",65,["road"],["vo2","endurance"]),
("run_hill_sprints","Hill Sprints","HILL",40,["hill"],["power","neuromuscular"]),
("run_hill_repeats","Hill Repeats","HILL",55,["hill"],["strength","climb"]),
("run_hilly_endurance","Hilly Endurance","HILL",70,["hill","trail"],["strength","aerobic"]),
("run_trail_technical","Technical Trail","TRAIL",65,["trail","technical"],["agility","technical"]),
("run_trail_climb","Trail Climb","TRAIL",75,["trail","mountain"],["climb","vertical"]),
("run_trail_descent","Trail Descent Skill","TRAIL",55,["trail","downhill"],["descent","skill"]),
("run_raid_transition","RAID Transition Run","RAID",50,["mixed"],["raid","transition"]),
("run_raid_loaded","RAID Loaded Run","RAID",60,["mixed"],["raid","loaded"]),
("run_raid_obstacle","RAID Obstacle Run","RAID",65,["mixed","trail"],["raid","obstacle"]),
("run_fartlek","Fartlek","INTERVAL",50,["road","trail"],["speed_play","mixed"]),
("run_mixed_terrain","Mixed Terrain Run","ENDURANCE",70,["mixed"],["aerobic","terrain"]),
]

RUNNING_FAMILIES = [
    RunningFamily(fid, name, RunningFamilyType[typ], dur, terrain, tags)
    for fid, name, typ, dur, terrain, tags in _RUNNING_RAW
]

def get_running_families() -> list[RunningFamily]:
    return list(RUNNING_FAMILIES)

def get_running_family_count() -> int:
    return len(RUNNING_FAMILIES)
