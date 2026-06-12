from .models import GeneratedRunSession
from .readiness_engine import readiness_score, readiness_zone
from .fatigue_engine import fatigue_ratio, fatigue_zone
from .session_selector import select_family
from .session_modifier import modify_session
from .intensity_governor import governor_accept
from .terrain_adapter import adapt_terrain
from .raid_adapter import adapt_raid
from .template_factory import ALL_TEMPLATES

def generate_session(
    goal: str = "raid",
    phase: str = "build",
    availability_min: int = 90,
    terrain: str = "trail",
    sleep: float = 80,
    fatigue: float = 80,
    stress: float = 80,
    motivation: float = 80,
    recovery: float = 80,
    acute_load: float = 100,
    chronic_load: float = 100,
    history: list[dict] | None = None,
):
    history = history or []
    r_score = readiness_score(sleep, fatigue, stress, motivation, recovery)
    r_zone = readiness_zone(r_score)
    f_zone = fatigue_zone(fatigue_ratio(acute_load, chronic_load))
    family = select_family(goal, phase, availability_min, r_zone, f_zone, terrain)
    modified = modify_session(family.id, availability_min)
    accepted, load_adj, reason = governor_accept(family.category, history, r_zone, f_zone)
    if not accepted:
        family = select_family("recovery", "base", availability_min, r_zone, f_zone, terrain)
        modified = modify_session(family.id, availability_min)
    template_id = f"{family.id}_intermediate"
    if not any(t.id == template_id for t in ALL_TEMPLATES):
        template_id = ALL_TEMPLATES[0].id
    session = GeneratedRunSession(
        family_id=family.id,
        template_id=template_id,
        variant=modified.variant,
        duration_min=availability_min,
        structure=modified.structure,
        category=family.category,
        terrain_type=terrain,
        expected_load=round(modified.expected_load * load_adj * availability_min, 1),
        target_type="pace",
        pace_target="free",
        tags=list(family.tags),
    )
    session = adapt_terrain(session, terrain)
    if goal == "raid":
        session = adapt_raid(session, phase)
    return session
