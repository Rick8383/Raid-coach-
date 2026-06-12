from .models import FitnessScore
from .utils import avg, clamp
class FitnessScoreEngine:
    def compute(self, recent_loads, performance_scores):
        score=clamp(avg(recent_loads)*0.45+avg(performance_scores)*0.55)
        label='excellent' if score>=85 else 'strong' if score>=70 else 'developing' if score>=55 else 'base'
        return FitnessScore(score,label)
