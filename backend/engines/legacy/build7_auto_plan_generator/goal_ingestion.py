
from .models import GoalInput, GoalType
class GoalIngestionEngine:
    def ingest(self, goal_type: str, target_event: str, duration_weeks: int, priority: str='A', target_level: str='competitive') -> GoalInput:
        if duration_weeks not in {8,12,16,24}: raise ValueError('duration_weeks must be 8, 12, 16 or 24')
        return GoalInput(GoalType(goal_type), target_event, duration_weeks, priority, target_level)
