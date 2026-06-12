from .models import RunCategory

def adapt_terrain(session, terrain: str):
    session.terrain_type = terrain
    if terrain == "trail":
        session.target_type = "time_on_feet"
        session.pace_target = None
        session.rpe_target = 7
    elif terrain == "mountain":
        session.target_type = "elevation_gain"
        session.pace_target = None
        session.d_plus_target = 500 if session.category != RunCategory.LONG_RUN else 1000
    elif terrain == "hilly":
        session.target_type = "rpe"
        session.pace_target = None
        session.rpe_target = 7
    return session
