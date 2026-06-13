"""Construit une séance détaillée normalisée à partir de la décision du coach.

Un seul format de sortie, quel que soit le sport, pour que l'app n'ait qu'un
rendu générique à gérer (phases → items). Force et course passent par leurs
moteurs réels ; natation / récup / repos sont des templates de sécurité ;
crossfit s'appuie sur le générateur de WODs sélection officiels.
"""
from __future__ import annotations

from engines.strength.family_registry import get_strength_families

_STRENGTH_FAMILY_NAMES = {f.family_id: f.name for f in get_strength_families()}

_BLOCK_ROLES = {
    "main": "Bloc principal",
    "back": "Back-off",
    "accessory": "Accessoire",
    "acc": "Accessoire",
    "finisher": "Finisher",
    "core": "Gainage",
}

_METHOD_LABELS = {
    "standard": "", "cluster": "Cluster", "rest_pause": "Rest-pause",
    "myo_reps": "Myo-reps", "drop_set": "Drop-set", "contrast": "Contraste",
    "dynamic_effort": "Effort dynamique", "emom": "EMOM", "density": "Densité",
}


def _prettify(token: str) -> str:
    return token.replace("_", " ").strip().capitalize()


def _strength_phases(coach, payload: dict, duration_min: int) -> tuple[str, list]:
    s = coach.strength.generate(
        coach._strength_input(payload),  # noqa: SLF001
        week_in_block=payload.get("week_in_block", 0),
        weeks_to_goal=payload.get("weeks_to_main_goal"),
        athlete_level=payload.get("athlete_level", "intermediate"),
        raid_focus=True,
        recent_family_ids=payload.get("recent_family_ids", []),
        seed=payload.get("seed", payload.get("day_of_week", "")),
    )
    title = _STRENGTH_FAMILY_NAMES.get(s.family_id, "Séance force")
    items = []
    for b in s.blocks:
        role_key = b.movement_id.rsplit("_", 1)[-1]
        role = _BLOCK_ROLES.get(role_key, "Bloc")
        method = _METHOD_LABELS.get(b.method.value, "")
        meta_bits = [f"repos {b.rest_sec}s"]
        if method:
            meta_bits.insert(0, method)
        if b.intensity_pct:
            meta_bits.insert(0, f"{b.intensity_pct:.0f}% e1RM")
        items.append({
            "name": role,
            "prescription": f"{b.sets} × {b.reps}",
            "meta": " · ".join(meta_bits),
            "notes": b.notes or "",
        })
    phases = [
        {"kind": "warmup", "label": "Préparation", "items": [
            {"name": "Activation lombaire (sciatique)", "prescription": "8'",
             "meta": "McKenzie · gainage anti-flexion", "notes": ""},
            {"name": "Montée en charge progressive", "prescription": "2-3 séries légères",
             "meta": "", "notes": ""},
        ]},
        {"kind": "main", "label": f"{title} · {s.phase.value}", "items": items},
        {"kind": "cooldown", "label": "Retour au calme", "items": [
            {"name": "Étirements + respiration", "prescription": "6'",
             "meta": "", "notes": ""},
        ]},
    ]
    return title, phases


def _run_phases(coach, payload: dict, duration_min: int) -> tuple[str, list]:
    session = coach.run_session(payload, duration_min)
    title = coach._run_family_name(session.family_id)  # noqa: SLF001
    struct = session.structure
    main_items = []
    for blk in struct.get("main", []):
        variant = blk.get("variant", "")
        typ = _prettify(blk.get("type", ""))
        main_items.append({
            "name": typ or "Bloc principal",
            "prescription": variant,
            "meta": f"terrain {session.terrain_type}",
            "notes": "",
        })
    phases = [
        {"kind": "warmup", "label": "Échauffement", "items": [
            {"name": "Footing progressif + gammes", "prescription": f"{struct.get('warmup', 12)}'",
             "meta": "Z1→Z2", "notes": ""},
        ]},
        {"kind": "main", "label": "Corps de séance", "items": main_items},
        {"kind": "cooldown", "label": "Retour au calme", "items": [
            {"name": "Footing décrassage", "prescription": f"{struct.get('cooldown', 8)}'",
             "meta": "Z1", "notes": ""},
        ]},
    ]
    targets = []
    if session.pace_target and session.pace_target != "free":
        targets.append(f"Allure cible : {session.pace_target}")
    return title, phases, targets


def _crossfit_phases(coach, payload: dict) -> tuple[str, list]:
    seed = payload.get("seed", payload.get("day_of_week", "wod"))
    kind = payload.get("wod_kind", "death_by")  # death_by | time_cap
    wod = coach.selection_wod_variant(seed, kind)
    items = [{"name": line, "prescription": "", "meta": "", "notes": ""}
             for line in wod["description"]]
    phases = [
        {"kind": "warmup", "label": "Échauffement spécifique", "items": [
            {"name": "Cardio progressif + mobilité", "prescription": "10'", "meta": "", "notes": ""},
        ]},
        {"kind": "main", "label": wod["name"], "items": items},
        {"kind": "cooldown", "label": "Retour au calme", "items": [
            {"name": "Marche + respiration", "prescription": "5'", "meta": "", "notes": ""},
        ]},
    ]
    return wod["name"], phases


def _template_phases(items: list[dict]) -> list:
    return [{"kind": "main", "label": "Séance", "items": items}]


def _swim_phases() -> tuple[str, list]:
    phases = [
        {"kind": "warmup", "label": "Échauffement", "items": [
            {"name": "Nage souple", "prescription": "200 m", "meta": "respiration ample", "notes": ""}]},
        {"kind": "main", "label": "Corps de séance", "items": [
            {"name": "Crawl aérobie", "prescription": "6 × 50 m", "meta": "récup 20s", "notes": ""},
            {"name": "Travail apnée", "prescription": "4 × 25 m", "meta": "progressif", "notes": "ne jamais forcer, sortir à la moindre alerte"}]},
        {"kind": "cooldown", "label": "Retour au calme", "items": [
            {"name": "Nage très facile", "prescription": "100 m", "meta": "", "notes": ""}]},
    ]
    return "Natation récupération + apnée", phases


def _recovery_phases() -> tuple[str, list]:
    phases = _template_phases([
        {"name": "Mobilité hanche / chaîne postérieure", "prescription": "15'",
         "meta": "amplitude contrôlée", "notes": "priorité nerf sciatique"},
        {"name": "Cardio très facile (vélo/marche)", "prescription": "15-20'",
         "meta": "Z1", "notes": ""},
    ])
    return "Récupération active", phases


def _rest_phases() -> tuple[str, list]:
    phases = _template_phases([
        {"name": "Repos complet", "prescription": "—",
         "meta": "sommeil · hydratation · nutrition", "notes": "le repos n'est pas négociable aujourd'hui"},
    ])
    return "Repos", phases


def build_session(coach, payload: dict, decision: dict) -> dict:
    discipline = decision["best_action"]
    duration_min = decision["duration_min"]
    targets: list[str] = []

    if discipline == "strength":
        title, phases = _strength_phases(coach, payload, duration_min)
    elif discipline == "run":
        title, phases, run_targets = _run_phases(coach, payload, duration_min)
        targets += run_targets
    elif discipline == "crossfit":
        title, phases = _crossfit_phases(coach, payload)
    elif discipline == "swim":
        title, phases = _swim_phases()
    elif discipline == "recovery":
        title, phases = _recovery_phases()
    else:  # rest
        title, phases = _rest_phases()

    # Séance secondaire d'un jour OFF (ex : force le soir après le run)
    secondary = decision.get("secondary_action")
    if secondary and discipline != "rest":
        sec_payload = {**payload, "best_action": secondary}
        sec_decision = {**decision, "best_action": secondary, "secondary_action": None}
        sec = build_session(coach, sec_payload, sec_decision)
        phases.append({"kind": "finisher", "label": f"2e séance (soir) · {sec['title']}",
                       "items": [it for ph in sec["phases"] if ph["kind"] == "main"
                                 for it in ph["items"]]})

    return {
        "discipline": discipline,
        "title": title,
        "headline": decision["reason"],
        "duration_min": duration_min,
        "intensity_cap": decision["intensity_cap"],
        "phases": phases,
        "targets": targets,
        "safety_notes": decision.get("safety_notes", []),
        "alternatives": decision.get("alternatives", []),
        "coach_reason": decision["reason"],
    }
