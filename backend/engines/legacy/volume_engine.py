def weekly_volume_target(base_volume: float, week: int, deload: bool = False) -> float:
    if deload:
        return round(base_volume * 0.7, 2)
    return round(base_volume * (1 + min(max(week, 0), 12) * 0.03), 2)
