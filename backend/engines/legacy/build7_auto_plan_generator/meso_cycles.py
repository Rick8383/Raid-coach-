
from .models import GapAnalysis, MacroCycle, MesoCycle
class MesoCycleBuilder:
    def build(self, macro: MacroCycle, gaps: GapAnalysis) -> list[MesoCycle]:
        cycles=[]; remaining=macro.duration_weeks; focus_seed=gaps.primary_gaps or gaps.secondary_gaps or ['race_specificity']
        for idx, phase in enumerate(macro.phases, start=1):
            weeks=max(1, round(macro.duration_weeks/len(macro.phases)))
            if idx==len(macro.phases): weeks=remaining
            remaining-=weeks
            load={'base':75,'build':90,'specific':100,'taper':55}.get(phase,80)
            cycles.append(MesoCycle(idx,weeks,[phase]+focus_seed[:2],load))
        return cycles
