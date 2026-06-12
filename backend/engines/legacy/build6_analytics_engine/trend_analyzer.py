from .models import TrendResult, TrendDirection
from .utils import slope
class TrendAnalyzer:
    def analyze(self, values):
        if len(values)<2: return TrendResult(TrendDirection.STABLE,0.0,0.0)
        s=slope(values); delta=round(values[-1]-values[0],1); direction=TrendDirection.IMPROVING if s>0.8 else TrendDirection.DECLINING if s<-0.8 else TrendDirection.STABLE
        return TrendResult(direction,delta,s)
