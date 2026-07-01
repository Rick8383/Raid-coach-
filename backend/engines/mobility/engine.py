"""Module MOBILITÉ (style GOWOD) — routines quotidiennes ciblées.

Principes (littérature) :
- Étirements statiques ≥60 s cumulées par groupe/semaine améliorent l'amplitude
  (Thomas et al. 2018, Behm et al. 2016) ; le travail quotidien court bat la
  grosse séance hebdo pour le gain de ROM.
- Auto-massage rouleau : gain de ROM aigu sans perte de force (Wiewelhove
  et al. 2019, méta-analyse).
- Avant séance : mobilité DYNAMIQUE (pas de statique long → baisse transitoire
  de force si >60 s/groupe, Simic 2013). Après séance / le soir : statique long.
- Sciatique L5-S1 : jamais de flexion lombaire chargée ni d'étirement agressif
  de la chaîne postérieure en flexion complète ; neuroglisses doux ; gainage
  McGill (curl-up, side plank, bird dog) pour la stabilité.

Routine = focus (zone prioritaire dérivée de la séance du jour) + blocs
minutés. Déterministe : (focus, seed) → même routine.
"""
from __future__ import annotations

FOCUS_AREAS = ["hanches", "chevilles_mollets", "epaules", "thoracique",
               "chaine_posterieure", "full"]

# Exercice : (nom, consigne, secondes, par_côté, catégories)
# cat: dyn = dynamique (ok avant séance), stat = statique (après/soir),
# roll = auto-massage, core = stabilité McGill, nerve = neuroglisse doux.
_EX: dict[str, list[tuple[str, str, int, bool, str]]] = {
    "hanches": [
        ("90/90 transitions", "Assis, jambes en 90/90 ; bascule d'un côté à l'autre, buste droit.", 60, False, "dyn"),
        ("Fente basse (couch stretch mur)", "Genou au mur, bassin rétroversé, grandis-toi. Respire lentement.", 90, True, "stat"),
        ("Pigeon (fessier profond)", "Tibia avant incliné, bassin carré, penche-toi SANS arrondir le bas du dos.", 90, True, "stat"),
        ("Squat profond tenu (goblet ou mains)", "Talons au sol, coudes qui poussent les genoux, dos long.", 60, False, "stat"),
        ("Rotations internes actives (assis)", "Assis, pieds larges : laisse tomber les genoux d'un côté puis de l'autre.", 60, False, "dyn"),
        ("Rouleau fessiers/TFL", "Passe lentement, arrête-toi 20-30 s sur les points sensibles.", 60, True, "roll"),
        ("Ouverture dynamique de hanche (leg swing)", "Balancement contrôlé avant/arrière puis latéral, amplitude progressive.", 45, True, "dyn"),
    ],
    "chevilles_mollets": [
        ("Dorsiflexion au mur (genou vers mur)", "Pied à 8-10 cm du mur, genou vers le mur SANS lever le talon.", 60, True, "dyn"),
        ("Étirement mollet jambe tendue", "Talon au sol, jambe arrière tendue, pousse le mur.", 60, True, "stat"),
        ("Étirement soléaire (genou fléchi)", "Même position, genou arrière fléchi, talon au sol.", 60, True, "stat"),
        ("Rouleau mollets", "Lent, du tendon d'Achille au genou, pauses sur points durs.", 60, True, "roll"),
        ("Cercles de cheville en charge", "En fente, genou dessine des cercles au-dessus du pied.", 45, True, "dyn"),
        ("Marche talons/pointes", "10 m talons, 10 m pointes — réveil des releveurs.", 45, False, "dyn"),
    ],
    "epaules": [
        ("Passements de bâton (dislocates)", "Prise large, bras tendus, passe devant-derrière lentement.", 60, False, "dyn"),
        ("Suspension passive à la barre", "Accroche-toi, épaules détendues, respire (30-45 s).", 40, False, "stat"),
        ("Étirement pec au cadre de porte", "Coude à 90°, avance le buste, ne cambre pas.", 60, True, "stat"),
        ("Rotations externes coude au corps (élastique léger)", "Lent, contrôle le retour.", 45, True, "dyn"),
        ("Rouleau grand dorsal", "Allongé sur le côté, bras au-dessus de la tête, roule lentement.", 60, True, "roll"),
        ("Glissés au mur (wall slides)", "Dos au mur, monte les bras en gardant contact poignets/coudes.", 60, False, "dyn"),
    ],
    "thoracique": [
        ("Extension thoracique sur rouleau", "Rouleau sous les omoplates, mains derrière la tête, étends SANS cambrer les lombaires.", 60, False, "roll"),
        ("Rotation thoracique quadrupédie (thread the needle)", "Main derrière la tête, ouvre le coude vers le plafond, expire.", 45, True, "dyn"),
        ("Cat-camel doux", "Amplitude CONFORTABLE, fluide — échauffement du dos (McGill).", 45, False, "dyn"),
        ("Prière étirée (child pose bras longs)", "Fesses vers talons, mains loin devant ; si sciatique sensible, reste haut.", 60, False, "stat"),
        ("Ouverture livre (open book) allongé", "Sur le côté, genoux pliés, ouvre le bras supérieur en suivant des yeux.", 45, True, "dyn"),
    ],
    "chaine_posterieure": [
        ("Neuroglisse sciatique DOUX", "Assis, dos NEUTRE : étends le genou + cheville flexion, redescends. Jamais de douleur.", 45, True, "nerve"),
        ("Ischio au sol jambe verticale (sangle)", "Allongé dos neutre, jambe tenue par une sangle, genou quasi tendu.", 75, True, "stat"),
        ("Bon étirement du psoas (fente haute)", "Bassin rétroversé, fessier serré, monte le bras du côté arrière.", 60, True, "stat"),
        ("Rouleau ischio-jambiers", "Lent, sans écraser ; pauses respirées.", 60, True, "roll"),
        ("Hip hinge au bâton", "Bâton en contact tête-dos-sacrum, hanche vers l'arrière — schéma de charnière.", 60, False, "dyn"),
    ],
    "core_mcgill": [
        ("Curl-up McGill", "Mains sous les lombaires, décolle tête+épaules 8 s, 6-4-2 répétitions.", 90, False, "core"),
        ("Side plank", "Genoux ou pieds, alignement strict, 6-4-2 × 8 s par côté.", 90, True, "core"),
        ("Bird dog", "Bras/jambe opposés, bassin immobile, 8 s par répétition, 6-4-2.", 90, False, "core"),
    ],
}

# Focus conseillé selon la séance principale du jour.
_FOCUS_BY_SESSION = {
    "run": "chevilles_mollets",
    "strength_push": "epaules",
    "strength_pull": "thoracique",
    "strength_legs": "hanches",
    "strength_fullbody": "hanches",
    "crossfit": "epaules",
    "swim": "thoracique",
    "rest": "full",
}


def focus_for(session_type: str, sub: str | None = None) -> str:
    key = f"{session_type}_{sub}" if session_type == "strength" and sub else session_type
    return _FOCUS_BY_SESSION.get(key, "full")


def _pick(pool: list, k: int, seed: int) -> list:
    out, idx = [], seed
    p = list(pool)
    for _ in range(min(k, len(p))):
        out.append(p.pop(idx % len(p)))
        idx = idx * 7 + 3
    return out


def generate_mobility(focus: str = "full", duration_min: int = 12,
                      seed: int = 1, sciatic: bool = True,
                      moment: str = "soir") -> dict:
    """Routine mobilité minutée. moment='avant' → dynamique seulement
    (pas de statique long avant l'effort) ; 'soir' → statique + rouleau."""
    if focus not in FOCUS_AREAS:
        focus = "full"
    if focus == "full":
        pool = [e for zone in ("hanches", "chevilles_mollets", "epaules",
                               "thoracique", "chaine_posterieure")
                for e in _EX[zone]]
    else:
        pool = list(_EX[focus])
        # complète avec la chaîne postérieure (priorité sciatique)
        pool += _EX["chaine_posterieure"][:2]

    if moment == "avant":
        pool = [e for e in pool if e[4] in ("dyn", "roll")]

    budget = max(6, duration_min) * 60
    core = _EX["core_mcgill"] if sciatic and moment != "avant" else []
    core_cost = sum(sec * (2 if per_side else 1) for _, _, sec, per_side, _ in core)
    budget_ex = budget - (core_cost if core else 0)

    picked, blocks, used = _pick(pool, 12, seed), [], 0
    for name, cue, sec, per_side, cat in picked:
        cost = sec * (2 if per_side else 1)
        if used + cost > budget_ex:
            continue
        used += cost
        label = f"{name} — {sec}s" + (" / côté" if per_side else "")
        blocks.append(f"{label} · {cue}")
    for name, cue, sec, per_side, _cat in core:
        label = f"{name} — {sec}s" + (" / côté" if per_side else "")
        blocks.append(f"{label} · {cue}")

    total_min = round((used + (core_cost if core else 0)) / 60)
    return {
        "type": "mobility",
        "focus": focus,
        "moment": moment,
        "title": f"Mobilité — {focus.replace('_', ' ')} {total_min}'",
        "duration_min": max(total_min, 6),
        "blocks": blocks,
        "note": ("Respiration lente (4-6 s d'expire) sur chaque position. "
                 "Sciatique : dos NEUTRE, jamais de douleur irradiante — si ça irradie, recule."
                 if sciatic else "Respiration lente sur chaque position."),
    }
