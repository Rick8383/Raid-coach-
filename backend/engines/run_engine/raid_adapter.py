def adapt_raid(session, phase: str = "build", carry_score: float = 60, mountain_score: float = 60):
    if "raid" not in session.family_id:
        if session.category.value in {"tempo", "threshold"}:
            session.family_id = "raid_tempo_hybrid" if session.category.value == "tempo" else "raid_threshold_hybrid"
        elif session.category.value == "long_run":
            session.family_id = "full_raid_simulation"
    if carry_score < 55:
        session.tags.append("carry_priority")
    if mountain_score < 55:
        session.tags.append("climb_priority")
        session.d_plus_target = max(session.d_plus_target or 0, 400)
    session.tags.append("raid_specific")
    return session
