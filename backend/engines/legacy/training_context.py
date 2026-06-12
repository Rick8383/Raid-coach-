from dataclasses import dataclass

@dataclass
class TrainingContext:
    readiness: float = 75
    fatigue: float = 35
    available_time_min: int = 60
