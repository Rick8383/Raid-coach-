def progression_factor(week: int, readiness: float = 75) -> float:
    base = 1.0 + min(max(week, 0), 12) * 0.025
    if readiness < 50:
        base *= 0.85
    return round(base, 2)
