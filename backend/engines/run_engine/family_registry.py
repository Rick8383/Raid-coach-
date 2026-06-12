from .models import RunCategory, RunFamily

def _slug(name: str) -> str:
    return (name.lower().replace("+", "plus").replace("/", "_").replace("-", "_")
            .replace(" ", "_").replace("'", "").replace("__", "_"))

_CATEGORIES = [
    (RunCategory.RECOVERY, ["Easy Run","Easy Progressive","Recovery Strides","Recovery Trail","Recovery Hills","Recovery HR Cap","Post WOD Recovery","Active Recovery","Recovery Endurance","Recovery Mixed Terrain"], 1),
    (RunCategory.Z2, ["Continuous Base","Long Z2","Progressive Z2","Split Z2","Terrain Z2","Aerobic Builder","Low HR Builder","Endurance Extension","Double Base","Base Finish Fast"], 2),
    (RunCategory.FARTLEK, ["Classic Fartlek","Pyramid Fartlek","Random Fartlek","Trail Fartlek","Long Surge","Short Surge","Descending Fartlek","Ascending Fartlek","Mixed Pace","Race Simulation Fartlek"], 3),
    (RunCategory.TEMPO, ["Continuous Tempo","Progressive Tempo","Tempo Blocks","Tempo Pyramid","Tempo Descending","Tempo Ascending","Half Marathon Tempo","Fast Finish Tempo","Broken Tempo","RAID Tempo"], 4),
    (RunCategory.THRESHOLD, ["Cruise Intervals","Long Threshold","Split Threshold","Threshold Pyramid","Threshold Progression","Threshold Descending","Threshold Ascending","Threshold Trail","Threshold Combo","Race Threshold"], 5),
    (RunCategory.VMA_SHORT, ["30 30","45 15","200m Repeats","300m Repeats","Sprint Ladder","Speed Pyramid","Cluster Speed","Descending Speed","Ascending Speed","Mixed VMA"], 5),
    (RunCategory.VMA_LONG, ["400m Repeats","600m Repeats","800m Repeats","1000m Repeats","Long Pyramid","VO2 Builder","VO2 Progression","Descending VO2","Ascending VO2","Mixed Long VMA"], 5),
    (RunCategory.HILLS, ["Short Hills","Long Hills","Power Hills","Strength Hills","Downhill Control","Hill Pyramid","Mixed Gradient","Trail Climb","RAID Climb","Hill Combo"], 4),
    (RunCategory.LONG_RUN, ["Easy Long Run","Progressive Long Run","Fast Finish Long Run","Long Run Tempo Insert","Long Run Threshold Insert","Trail Long Run","RAID Long Run","Double Terrain Long Run","Fatigue Long Run","Ultra Builder"], 3),
    (RunCategory.RAID, ["Run Ruck Combo","Run WOD Combo","Long Climb Session","Obstacle Simulation","Hybrid Endurance","Back to Back Endurance","Multi Surface RAID","RAID Tempo Hybrid","RAID Threshold Hybrid","Full RAID Simulation"], 5),
    (RunCategory.TEST, ["Cooper Test","5K Test","10K Test","Threshold Test","VMA Test","Hill Test","Endurance Test","RAID Readiness Test","Hybrid Test","Benchmark Test"], 4),
]

RUN_FAMILIES: list[RunFamily] = []
for category, names, base_difficulty in _CATEGORIES:
    for name in names:
        difficulty = min(5, base_difficulty + (1 if category in {RunCategory.RAID, RunCategory.TEST} else 0))
        RUN_FAMILIES.append(RunFamily(id=_slug(name), name=name, category=category, difficulty=difficulty, tags=[category.value]))

assert len(RUN_FAMILIES) == 110
