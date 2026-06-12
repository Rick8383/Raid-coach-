def clamp(value, low=0.0, high=100.0): return round(max(low,min(high,float(value))),1)
def avg(values, default=0.0): return sum(values)/len(values) if values else default
def slope(values):
    if len(values)<2: return 0.0
    n=len(values); xm=(n-1)/2; ym=avg(values); den=sum((i-xm)**2 for i in range(n))
    return round(sum((i-xm)*(v-ym) for i,v in enumerate(values))/den,3) if den else 0.0
