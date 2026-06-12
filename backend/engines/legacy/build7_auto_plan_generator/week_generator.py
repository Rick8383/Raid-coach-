
from .models import MesoCycle, WeeklyPlan
LIB={'base':['Z2 endurance','strength foundation','mobility','easy trail'],'build':['tempo','hill strength','loaded carry','recovery'],'specific':['race simulation','technical trail','portage intervals','recovery'],'taper':['short intensity','mobility','easy run','rest']}
class AutoWeekGenerator:
    def generate(self, meso_cycles: list[MesoCycle]) -> list[WeeklyPlan]:
        weeks=[]; n=1
        for m in meso_cycles:
            sessions=LIB.get(m.focus[0], LIB['build'])
            for _ in range(m.weeks): weeks.append(WeeklyPlan(n,m.focus,sessions.copy(),m.load_target)); n+=1
        return weeks
