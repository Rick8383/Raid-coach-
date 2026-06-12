
from .models import WeeklyPlan, DailyPlan
class AutoDailyGenerator:
    def generate(self, weeks: list[WeeklyPlan]) -> list[DailyPlan]:
        days=[]; d=1
        for w in weeks:
            for s in w.sessions:
                days.append(DailyPlan(d,w.week_number,s,f'Week {w.week_number}: {", ".join(w.focus[:2])}',round(w.load_target/max(1,len(w.sessions)),1))); d+=1
        return days
