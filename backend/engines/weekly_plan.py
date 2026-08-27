"""Plan glissant détaillé (Mission 1B) — N semaines jour par jour.

Assemble, pour chaque jour, les séances réelles via les générateurs :
- course (Mission 2), force 5/3/1 (Mission 4), WOD (Mission 3), natation/récup.
Respecte le planning police 3/2/2/3 (jour OFF = double séance possible, jour de
service = séance unique courte, dimanche petite semaine = natation récup).

Le 5/3/1 progresse avec le calendrier : semaine_dans_cycle = (W % 4) + 1,
cycle = W // 4 (W = index de semaine absolu depuis l'ancre 2026-06-15).
"""
from __future__ import annotations

from datetime import date, timedelta

from engines import schedule as _sched
from engines.schedule import user_schedule as _us
from engines import mobility as _mob
from engines.run_generator import generate_run
from engines.strength_531 import generate_strength_531
from engines.wod_generator import generate_wod

START = date(2026, 6, 15)   # ancre lundi, grande semaine

# Templates hebdo : weekday (0=lun..6=dim) -> liste de specs séance.
# spec = (moment, type, sous-type)  ; sous-type = run_type ou jour force.
#
# RÈGLES STRUCTURANTES (contraintes réelles de l'athlète) :
#  1. Un JOUR DE SERVICE ne porte qu'UNE SEULE séance — jamais de double. Il a
#     un créneau sport au travail : cette séance PEUT donc être de la force.
#  2. JAMAIS deux séances de force le même jour.
#  3. Un JOUR OFF peut porter un double (course/WOD le matin + force le soir).
# → push, pull et legs restent trois séances distinctes, réparties sur des jours
#   différents, chaque semaine.
_BIG_WORK = {   # service lun/mar/ven/sam/dim ; OFF mer/jeu
    0: [("matin", "strength", "push")],                                 # lun service — SEULE séance (créneau sport)
    1: [("matin", "run", "tempo")],                                     # mar service — SEULE séance
    2: [("matin", "run", "vma_courte"), ("soir", "strength", "pull")],  # mer OFF — DOUBLE
    3: [("matin", "crossfit", None), ("soir", "strength", "legs")],     # jeu OFF — DOUBLE
    4: [("matin", "run", "seuil")],                                     # ven service — SEULE séance
    5: [("matin", "run", "z2")],                                        # sam service — SEULE séance
    6: [("matin", "swim", None)],                                       # dim service — récup
}
_SMALL_WORK = {  # service mer/jeu ; OFF le reste
    0: [("matin", "run", "vma_courte"), ("soir", "strength", "push")],  # lun OFF — DOUBLE
    1: [("matin", "run", "cotes"), ("soir", "strength", "pull")],       # mar OFF — DOUBLE
    2: [("matin", "strength", "legs")],                                 # mer service — SEULE séance (créneau sport)
    3: [("matin", "run", "z2")],                                        # jeu service — SEULE séance
    4: [("matin", "run", "vma_longue"), ("soir", "crossfit", None)],    # ven OFF — DOUBLE
    5: [("matin", "run", "z2")],                                        # sam OFF — sortie longue
    6: [("matin", "swim", None)],                                       # dim OFF — récup
}

# Répartition des 3 séances de force : 2 sur les jours OFF (en double avec la
# course ou le WOD) et 1 sur un jour de service, où elle est la SEULE séance de
# la journée — l'athlète y a un créneau sport dédié. Aucun jour ne porte deux
# séances de force, et aucun jour de service ne porte deux séances tout court.
# (Le type de séance combinée `upper` reste disponible via
# /generate/strength?day=upper pour qui préfère condenser en 2 séances.)


def _swim_session() -> dict:
    return {"title": "Natation récupération + apnée", "duration_min": 40,
            "detail": {"blocks": ["200m échauffement souple",
                                  "6×50m crawl aérobie (récup 20s)",
                                  "4×25m apnée progressive (jamais forcer)",
                                  "100m retour au calme"]}}


def _build_session(spec, w_index, weekday, vma, fcmax, maxes=None):
    moment, stype, sub = spec
    if stype == "run":
        seed = ((w_index * 3 + weekday) % 100) + 1
        # w_index = index de semaine du plan → volume progressif et cohérent.
        detail = generate_run(sub, seed, vma, fcmax, progress=w_index)
        dur = detail["duration_min"]
        title = detail["title"]
        # Pliométrie légère + sprints en côte 1×/semaine (jour VMA courte) :
        # améliore l'économie de course sans volume ajouté (Balsalobre 2016 ;
        # Rønnestad & Mujika 2014). Volume bas, progressif, sciatique-safe
        # (réception amortie, pas de contact lombaire).
        if sub == "vma_courte":
            level = min(3, w_index // 4)   # progression par cycle de 4 semaines
            detail["plyo_finisher"] = {
                "title": "Pliométrie + côtes (8-10', après la séance)",
                "blocks": [
                    f"{3 + level}×20 m sprint en côte (4-6 %), marche de retour",
                    f"{2 + level}×8 foulées bondissantes, récup 60 s",
                    f"2×{8 + 2 * level} sauts corde pieds joints (souples, silencieux)",
                    "Réceptions AMORTIES genoux souples — stop si gêne sciatique.",
                ],
            }
            dur += 10
    elif stype == "strength":
        week_in_cycle = (w_index % 4) + 1
        cycle = w_index // 4
        # variant = jour de la semaine → deux séances full body de la même semaine
        # ne proposent pas les mêmes mouvements.
        detail = generate_strength_531(sub, week_in_cycle, cycle, maxes, variant=weekday)
        if sub == "fullbody":
            dur = 75 if week_in_cycle != 4 else 60   # full body : 1h-1h15 max
            title = f"Force FULL BODY — S{week_in_cycle}" + (" deload" if week_in_cycle == 4 else "")
        else:
            dur = 70 if week_in_cycle != 4 else 55
            label = "HAUT DU CORPS (push+pull)" if sub == "upper" else sub.upper()
            title = f"Force {label} — S{week_in_cycle}" + (" deload" if week_in_cycle == 4 else "")
    elif stype == "crossfit":
        # Rotation des formats (variety_index) + durée variable : deux WOD
        # consécutifs du plan ne partagent ni le format ni le gabarit. Avec un
        # tirage purement aléatoire, les mêmes formats retombaient à quelques
        # jours d'intervalle → sensation de monotonie.
        vidx = w_index * 7 + weekday
        cap = 12 + (vidx % 4) * 2          # 12 / 14 / 16 / 18 min
        detail = generate_wod("auto", cap, f"plan_{w_index}_{weekday}",
                              exclude_lumbar=True, variety_index=vidx)
        dur = 20 + cap                      # échauffement + WOD
        title = detail["name"]
    else:  # swim
        sw = _swim_session()
        return {"moment": moment, "type": "swim", "title": sw["title"],
                "duration_min": sw["duration_min"], "detail": sw["detail"]}
    return {"moment": moment, "type": stype, "title": title, "duration_min": dur, "detail": detail}


def _day_payload(d: date, shift_weeks: int, vma: float, fcmax: int,
                 config: dict | None = None, maxes: dict | None = None) -> dict:
    # La STRUCTURE (jours d'entraînement, type de semaine) suit le RYTHME de
    # l'athlète (config) calé sur le calendrier réel ; seule la PROGRESSION
    # (cycle 5/3/1, seeds) peut être décalée (shift_weeks) — mode standby.
    cfg = _us.normalize(config)
    real_monday = d - timedelta(days=d.weekday())
    ds = _us.day_schedule(cfg, d)
    wt = ds["week_type"]
    # Progression 5/3/1 relative au J0 de l'athlète (ancre police / start weekly)
    # → chacun démarre au cycle 0 à sa date de début (et le propriétaire peut
    # redémarrer le programme en re-fixant son ancre).
    real_w = max(0, (real_monday - _us.plan_start(cfg)).days // 7)
    plan_w = max(0, real_w - max(0, int(shift_weeks)))
    template = _us.week_template(cfg, plan_w, wt, _BIG_WORK, _SMALL_WORK)
    specs = template[d.weekday()]
    if cfg.get("training_style") == "fullbody":
        # En full body, toute séance de force devient une séance corps entier.
        specs = [(m, t, "fullbody") if t == "strength" else (m, t, s) for (m, t, s) in specs]
    sessions = [_build_session(spec, plan_w, d.weekday(), vma, fcmax, maxes)
                for spec in specs]
    # SEMAINE DE TESTS toutes les 6 semaines (S6, S12, S18…) : le dimanche, la
    # séance du jour est remplacée par la batterie de tests RAID → progression
    # objective vers les barèmes (Cooper, Luc Léger, tractions, pompes, corde).
    if plan_w % 6 == 5 and d.weekday() == 6:
        n_test = plan_w // 6 + 1
        sessions = [{
            "moment": "matin", "type": "crossfit",
            "title": f"TESTS RAID — batterie n°{n_test}",
            "duration_min": 60,
            "detail": {
                "name": f"TESTS RAID — batterie n°{n_test}",
                "format": "TEST", "duration_or_cap": "60' avec récup complètes",
                "description": [
                    "Cooper 12 min — distance max (objectif : ≥ 3000 m)",
                    "Récup 10-15 min marche/trot très facile",
                    "Tractions strictes — max sans lâcher la barre (objectif : ≥ 15)",
                    "Pompes — max en 2 min (objectif : ≥ 50)",
                    "Montée de corde 5 m si dispo (objectif : sans les jambes)",
                    "→ Note chaque résultat dans l'onglet TESTS pour suivre la courbe.",
                ],
                "target_score": "Bat tes chiffres de la batterie précédente",
                "muscles": "test global (aérobie + tirage + poussée)",
                "lumbar_safe": True,
                "lumbar_note": "Échauffement complet avant chaque test ; gainage neutre sur les tractions.",
            },
        }]
    # Mobilité quotidienne (style GOWOD) : 10-12' le soir, focus dérivé de la
    # séance principale du jour (jour off → routine complète). Le travail
    # QUOTIDIEN court est le plus efficace pour gagner de l'amplitude
    # (Thomas 2018) ; sciatique-safe (McGill inclus, dos neutre).
    if specs:
        m_focus = _mob.focus_for(specs[0][1], specs[0][2])
    else:
        m_focus = "full"
    mob = _mob.generate_mobility(m_focus, 12 if specs else 18,
                                 seed=plan_w * 7 + d.weekday() + 1)
    sessions.append({"moment": "soir", "type": "recovery", "title": mob["title"],
                     "duration_min": mob["duration_min"],
                     "detail": {"blocks": mob["blocks"], "note": mob["note"],
                                "mobility": True, "focus": mob["focus"]}})
    return {
        "date": d.isoformat(),
        "day_of_week": ds["day_of_week"],
        "is_work_day": ds["is_work_day"],
        "week_type": wt,
        "week_index": plan_w,
        "sessions": sessions,
    }


def build_day(d: date, vma: float = 14.0, fcmax: int = 186, shift_weeks: int = 0,
              config: dict | None = None, maxes: dict | None = None) -> dict:
    """Séances planifiées pour une date — MÊME source que build_weekly (mêmes
    seeds), calées sur le RYTHME (config) et le NIVEAU (maxes = 1RM) de l'athlète.
    `shift_weeks` décale la progression (standby) sans toucher au calendrier."""
    return _day_payload(d, shift_weeks, vma, fcmax, config, maxes)


def build_weekly(from_week: int = 0, n: int = 6, vma: float = 14.0, fcmax: int = 186,
                 config: dict | None = None, maxes: dict | None = None) -> dict:
    from_week = max(0, min(int(from_week), 200))
    n = max(1, min(int(n), 12))
    weeks = []
    for offset in range(n):
        w_index = from_week + offset
        monday = START + timedelta(weeks=w_index)
        days = [_day_payload(monday + timedelta(days=wd), 0, vma, fcmax, config, maxes)
                for wd in range(7)]
        weeks.append({"week_index": w_index, "monday": monday.isoformat(),
                      "week_type": days[0]["week_type"], "days": days})
    return {"from_week": from_week, "n": n, "weeks": weeks}
