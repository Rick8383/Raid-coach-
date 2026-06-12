from dataclasses import dataclass

@dataclass
class AthleteProfile:
    athlete_id: str
    level: str = "intermediate"
    goal: str = "operational"
