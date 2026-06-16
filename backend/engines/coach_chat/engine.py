"""Moteur du Coach Chat.

Principe : pas de LLM externe (offline-first, déterministe, testable). On
détecte l'intention par mots-clés pondérés, puis on compose une réponse
personnalisée à partir du `context` (profil, métriques du jour, planning) que
la couche API assemble depuis le store.

`answer(message, context)` renvoie :
    {
      "reply": str,            # texte de la réponse (markdown léger)
      "topic": str,            # intention détectée
      "suggestions": [str],    # questions de relance proposées
    }
"""
from __future__ import annotations

import re
import unicodedata

# --- Échelle RPE (source de vérité partagée avec l'app pour les tooltips) ---
# Borg CR10 adaptée entraînement (RPE de séance / par série).
RPE_SCALE: list[dict] = [
    {"value": 1, "label": "Très très facile", "zone": "Récupération",
     "desc": "Effort à peine perceptible, conversation sans aucune gêne."},
    {"value": 2, "label": "Très facile", "zone": "Récupération",
     "desc": "Footing de décrassage, tu pourrais tenir des heures."},
    {"value": 3, "label": "Facile", "zone": "Endurance Z1-Z2",
     "desc": "Confortable, respiration libre, tu parles en phrases complètes."},
    {"value": 4, "label": "Modéré", "zone": "Endurance Z2",
     "desc": "Soutenu mais maîtrisé, conversation par phrases courtes."},
    {"value": 5, "label": "Modéré +", "zone": "Tempo / Z3 bas",
     "desc": "Ça commence à pousser, respiration plus marquée."},
    {"value": 6, "label": "Difficile", "zone": "Tempo / Z3",
     "desc": "Inconfort net, quelques mots seulement entre les respirations."},
    {"value": 7, "label": "Très difficile", "zone": "Seuil / Z4",
     "desc": "Dur. En force : ~3-4 reps en réserve (RIR). Tu ne parles plus."},
    {"value": 8, "label": "Très très difficile", "zone": "Seuil haut / Z4-Z5",
     "desc": "Très exigeant. En force : ~2 reps en réserve. Respiration haletante."},
    {"value": 9, "label": "Quasi maximal", "zone": "VO2max / Z5",
     "desc": "Proche de la limite. En force : 1 rep en réserve (RIR 1)."},
    {"value": 10, "label": "Maximal", "zone": "Sprint / 1RM",
     "desc": "Effort total, rien en réserve. À réserver aux tests et finishers."},
]
_RPE_BY_VALUE = {r["value"]: r for r in RPE_SCALE}


def _norm(text: str) -> str:
    """Minuscule + sans accents, pour un matching robuste."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()


# Mots-clés par intention (déjà normalisés : sans accent, minuscule).
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "today": ["aujourd hui", "aujourdhui", "auj", "ce jour", "ce matin",
              "quoi faire", "je fais quoi", "seance du jour", "maintenant",
              "ma seance", "que faire"],
    "schedule": ["planning", "semaine", "grande semaine", "petite semaine",
                 "calendrier", "quand je travaille", "service", "off", "repos",
                 "jour off", "3/2/2/3", "rythme", "agenda"],
    "rpe": ["rpe", "intensite", "echelle", "borg", "rir", "reps en reserve",
            "difficulte ressentie", "c est quoi rpe"],
    "nutrition": ["nutrition", "manger", "macro", "macros", "calorie", "calories",
                  "proteine", "proteines", "glucide", "glucides", "lipide", "lipides",
                  "complement", "complements", "creatine", "whey", "cafeine",
                  "collagene", "omega", "magnesium", "electrolyte", "alimentation",
                  "poids", "secher", "seche", "prise de masse", "hydratation"],
    "strength": ["force", "musculation", "muscu", "531", "5/3/1", "developpe",
                 "developpe couche", "dc", "squat", "souleve", "deadlift", "ohp",
                 "rowing", "row", "charge", "charges", "1rm", "training max",
                 "progression", "tractions", "gtg"],
    "run": ["course", "courir", "run", "allure", "allures", "vma", "seuil",
            "fractionne", "fractionné", "tempo", "fartlek", "z2", "zone fc",
            "zones fc", "frequence cardiaque", "fcmax", "footing", "endurance",
            "cardio", "cote", "cotes"],
    "wod": ["wod", "crossfit", "amrap", "for time", "emom", "metcon", "hyrox",
            "chrono", "timer", "minuteur", "death by", "tabata", "rft", "chipper"],
    "sciatica": ["sciatique", "dos", "lombaire", "l5", "s1", "douleur", "mal de dos",
                 "hernie", "lumbago", "nerf"],
    "raid": ["raid", "selection", "epreuve", "epreuves", "2029", "rcos", "test physique",
             "objectif", "objectifs", "but"],
    "benchmarks": ["benchmark", "benchmarks", "test", "tests", "cooper", "record",
                   "pr", "tractions max", "montee de corde", "corde", "luc leger"],
    "recovery": ["recuperation", "recup", "sommeil", "dormir", "fatigue", "fatigue",
                 "repos", "hrv", "courbature", "courbatures", "deload", "surentrainement"],
    "help": ["aide", "help", "tu sais faire quoi", "que sais tu", "commandes",
             "bonjour", "salut", "hello", "coucou", "yo", "hey"],
}


def detect_topic(message: str) -> str:
    """Intention dominante par score de mots-clés (le plus long match l'emporte)."""
    n = _norm(message)
    best_topic, best_score = "fallback", 0.0
    for topic, keywords in _TOPIC_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in n:
                # Un mot-clé plus spécifique (plus long) pèse davantage.
                score += 1.0 + len(kw) / 40.0
        if score > best_score:
            best_topic, best_score = topic, score
    return best_topic


# --------------------------------------------------------------------------
# Composition des réponses (chaque handler reçoit le contexte normalisé)
# --------------------------------------------------------------------------
def _g(ctx: dict, *path, default=None):
    cur = ctx
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _profile_lines(ctx: dict) -> list[str]:
    p = ctx.get("profile") or {}
    out = []
    if p.get("weight_kg"):
        tw = p.get("target_weight_kg")
        out.append(f"Poids {p['weight_kg']} kg"
                   + (f" (objectif {tw} kg)" if tw else ""))
    if p.get("vma_kmh"):
        out.append(f"VMA {p['vma_kmh']} km/h")
    if p.get("fc_max"):
        out.append(f"FCmax {p['fc_max']} bpm")
    return out


def _h_help(ctx: dict) -> str:
    name = _g(ctx, "profile", "name")
    hello = f"Salut {name} ! " if name else "Salut ! "
    return (hello + "Je suis ton coach RAID. Je peux t'aider sur :\n"
            "• **Ta séance du jour** — « qu'est-ce que je fais aujourd'hui ? »\n"
            "• **Le planning 3/2/2/3** — grande/petite semaine, jours OFF\n"
            "• **La force 5/3/1** — charges, progression, objectifs 1RM\n"
            "• **La course** — allures, VMA, zones FC\n"
            "• **Les WOD** — formats, chrono compétition, score\n"
            "• **La nutrition** — macros, compléments, hydratation\n"
            "• **Le RPE** — comment coter l'intensité d'une séance\n"
            "• **La sciatique L5-S1** — adaptations sécurité\n"
            "• **La sélection RAID 2029** — épreuves, objectifs\n\n"
            "Pose ta question, je te réponds avec tes données réelles.")


def _h_today(ctx: dict) -> str:
    today = ctx.get("today") or {}
    metrics = ctx.get("metrics") or {}
    if not today:
        return ("Dis-moi la date ou ouvre l'onglet JOUR : je cale la séance sur "
                "ton planning 3/2/2/3 et ta readiness du matin.")
    wt = "grande semaine" if today.get("week_type") == "big_work" else "petite semaine"
    intent = (today.get("intent") or {}).get("label", "")
    work = "service" if today.get("is_work_day") else "OFF"
    lines = [f"On est en **{wt}**, jour **{work}**."]
    if intent:
        lines.append(f"Intention du jour : *{intent}*.")
    r = metrics.get("readiness")
    if r is not None:
        if r >= 70:
            lines.append(f"Ta readiness est bonne ({r:.0f}/100) → tu peux pousser "
                         "l'intensité prévue.")
        elif r >= 50:
            lines.append(f"Readiness moyenne ({r:.0f}/100) → garde le volume mais "
                         "plafonne l'intensité, reste sur la qualité.")
        else:
            lines.append(f"Readiness basse ({r:.0f}/100) → privilégie Z2 / mobilité, "
                         "ne force pas aujourd'hui.")
    if metrics.get("sciatic_flare") or metrics.get("pain_flag"):
        lines.append("⚠ Tu as signalé une douleur : on retire tout mouvement "
                     "lombaire et on reste prudent.")
    lines.append("Détail complet dans l'onglet JOUR (échauffement → corps → "
                 "retour au calme).")
    return "\n".join(lines)


def _h_schedule(ctx: dict) -> str:
    today = ctx.get("today") or {}
    base = ("Ton rythme police **3/2/2/3** (ancre : semaine du 15/06/2026 = grande "
            "semaine) :\n"
            "• **Grande semaine** — service lun/mar/ven/sam/dim, **OFF mer + jeu**.\n"
            "• **Petite semaine** — service mer/jeu, le reste OFF.\n\n"
            "Côté entraînement : un **jour OFF = double séance** (course + force), "
            "un **jour de service = séance courte de qualité**, et le **dimanche de "
            "petite semaine = natation récup**.")
    if today:
        wt = "grande" if today.get("week_type") == "big_work" else "petite"
        work = "service" if today.get("is_work_day") else "OFF"
        base += f"\n\nAujourd'hui : **{wt} semaine**, jour **{work}**."
    return base


def _h_rpe(ctx: dict) -> str:
    m = re.search(r"\b(10|[1-9])\b", _norm(ctx.get("_message", "")))
    if m:
        v = int(m.group(1))
        r = _RPE_BY_VALUE.get(v)
        if r:
            return (f"**RPE {v} — {r['label']}** ({r['zone']})\n{r['desc']}")
    lines = ["Le **RPE** (Rate of Perceived Exertion, échelle 1-10) cote la "
             "difficulté *ressentie* d'une séance ou d'une série. En force, on le "
             "relie aux **reps en réserve (RIR)**. Repères clés :"]
    for v in (4, 6, 7, 8, 9, 10):
        r = _RPE_BY_VALUE[v]
        lines.append(f"• **{v}** — {r['label']} : {r['desc']}")
    lines.append("\nDans l'app, survole (ou appuie sur) chaque chiffre RPE pour "
                 "voir son explication.")
    return "\n".join(lines)


def _h_nutrition(ctx: dict) -> str:
    p = ctx.get("profile") or {}
    w = p.get("weight_kg")
    n = _norm(ctx.get("_message", ""))
    if "creatine" in n:
        return ("**Créatine monohydrate** : 3-5 g/jour, tous les jours (timing "
                "indifférent), à vie tant que tu t'entraînes. Preuve A+ pour la "
                "force et la puissance répétée. Pas besoin de phase de charge.")
    if any(k in n for k in ("complement", "complements", "whey", "cafeine",
                            "omega", "magnesium")):
        return ("Compléments à preuve solide pour ton profil : **créatine** "
                "(3-5 g/j), **whey** (autour des séances), **caféine** (3-6 mg/kg "
                "avant un effort clé), **oméga-3**, **vit D3**, **magnésium** le "
                "soir, **électrolytes** sur les grosses séances. Détail complet "
                "(dose/timing/preuve) dans l'onglet NUTRITION → Compléments.")
    lines = ["Cadre nutrition (objectif recomposition + performance) :"]
    if w:
        prot = round(2.0 * w)
        lines.append(f"• **Protéines** ~{prot} g/j (2 g/kg) — plancher de sécurité "
                     "1,8 g/kg.")
        lines.append(f"• **Lipides** ≥ {round(0.8 * w)} g/j (0,8 g/kg mini, santé "
                     "hormonale).")
        lines.append("• **Glucides** : le reste des calories, concentrés autour des "
                     "séances dures.")
    else:
        lines.append("• Protéines ~2 g/kg, lipides ≥ 0,8 g/kg, glucides autour des "
                     "séances.")
    lines.append("• **Hydratation** : ~35 ml/kg + pertes à l'effort.")
    lines.append("\nL'onglet NUTRITION calcule tes macros exactes, convertit en "
                 "grammes d'aliments et vérifie les garde-fous (RED-S, lipides bas).")
    return "\n".join(lines)


def _h_strength(ctx: dict) -> str:
    cur = (_g(ctx, "profile", "current") or {})
    n = _norm(ctx.get("_message", ""))
    lines = ["Ta force suit un **5/3/1** (cycle 4 semaines : 5/5/5+, 3/3/3+, "
             "5/3/1+, deload). +2,5 kg sur le haut du corps et +5 kg sur le bas "
             "par cycle, via le **Training Max** (~90 % du 1RM)."]
    bench = cur.get("bench_ratio") or cur.get("bench_1rm") or cur.get("dc_1rm")
    squat = cur.get("squat_ratio") or cur.get("squat_1rm")
    if bench:
        lines.append(f"• **Développé couché** : 1RM ~{bench} kg → objectif **140 kg**.")
    if squat:
        lines.append(f"• **Squat** : 1RM ~{squat} kg → objectif **160 kg**.")
    if "traction" in n or "gtg" in n:
        lines.append("• **Tractions** : méthode Grease the Groove (séries "
                     "fréquentes loin de l'échec) le jour PULL.")
    lines.append("⚠ Sciatique L5-S1 : pas de soulevé de terre lourd → remplacé par "
                 "**hip thrust**, gainage Big 3 McGill obligatoire à l'échauffement.")
    lines.append("\nL'onglet SÉANCES → FORCE génère ta séance du jour et trace la "
                 "progression des charges sur 6 cycles.")
    return "\n".join(lines)


def _h_run(ctx: dict) -> str:
    p = ctx.get("profile") or {}
    vma = p.get("vma_kmh")
    fc = p.get("fc_max")
    lines = ["Côté course, 7 types de séances : VMA courte/longue, seuil, fartlek, "
             "tempo, Z2 (endurance), côtes."]
    if vma:
        z2 = round(vma * 0.65, 1)
        seuil = round(vma * 0.85, 1)
        lines.append(f"À partir de ta **VMA {vma} km/h** : endurance Z2 ~{z2} km/h "
                     f"(65 %), allure seuil ~{seuil} km/h (85 %), VO2max 95-105 %.")
    if fc:
        lines.append(f"Zones FC sur **FCmax {fc} bpm** : Z2 ~{round(fc*0.7)}-"
                     f"{round(fc*0.8)} bpm, seuil ~{round(fc*0.85)}-{round(fc*0.9)} bpm.")
    lines.append("L'onglet SÉANCES → COURSE génère une séance chiffrée (allures "
                 "km/h + min/km + % VMA, FC cible) ; les zones détaillées sont juste "
                 "en dessous.")
    return "\n".join(lines)


def _h_wod(ctx: dict) -> str:
    return ("Côté WOD/CrossFit : 15 formats (AMRAP, For Time, EMOM, Death By, "
            "Chipper, RFT, Tabata, Ladder, Pyramide…), avec garde-fou anti-lombaire "
            "activé par défaut (sciatique).\n\n"
            "Sur la page WOD, le **chrono de compétition** démarre par un compte à "
            "rebours de 15 s (réglable en cliquant dessus : countdown, time cap, "
            "mode) avec des bips. Il **compte le temps** sur les For Time et "
            "**compte les reps/rounds** sur les AMRAP → ton **score** est enregistré "
            "dans l'agenda pour le suivi.")


def _h_sciatica(ctx: dict) -> str:
    return ("Protocole **sciatique L5-S1** appliqué partout dans l'app :\n"
            "• WOD : exclusion des mouvements lombaires (deadlift, GHD, good "
            "morning, snatch lourd…) — ON par défaut, jamais en finisseur.\n"
            "• Force : soulevé de terre lourd remplacé par **hip thrust**, **Big 3 "
            "McGill** (curl-up, side plank, bird-dog) à chaque échauffement.\n"
            "• En cas de douleur signalée au check-in : intensité plafonnée, "
            "bascule vers mobilité / Z2.\n\n"
            "Si la douleur irradie dans la jambe ou s'aggrave : repos et avis "
            "médical, on ne force jamais sur un nerf.")


def _h_raid(ctx: dict) -> str:
    weeks = _g(ctx, "weeks_to_goal")
    base = ("Cap : **sélection RAID 2029**. L'app rétro-planifie jusque-là "
            "(macro-périodisation BASE → BUILD → PEAK → TRANSITION).\n"
            "Objectifs élite visés : DC 140 kg, Squat 160 kg, VMA en hausse, "
            "tractions/corde, endurance lestée — suivis dans l'onglet OBJECTIFS.")
    if weeks:
        base += f"\n\nIl reste ~**{weeks} semaines** avant l'échéance visée."
    return base


def _h_benchmarks(ctx: dict) -> str:
    return ("Tes **benchmarks** (Cooper, tractions max, montée de corde, WOD de "
            "référence, 1RM) se saisissent et se tracent dans l'onglet OBJECTIFS : "
            "chaque test du jour alimente le graphe de progression. Re-teste toutes "
            "les 4-6 semaines (fin de bloc) pour recaler allures et charges.")


def _h_recovery(ctx: dict) -> str:
    metrics = ctx.get("metrics") or {}
    lines = ["Récupération : le sommeil et la HRV pilotent ta readiness, donc la "
             "charge autorisée (boucle adaptative ACWR + budget fatigue)."]
    r = metrics.get("readiness")
    f = metrics.get("fatigue")
    if r is not None or f is not None:
        lines.append(f"Aujourd'hui : readiness {r if r is not None else '—'} / "
                     f"fatigue {f if f is not None else '—'}.")
    lines.append("Une semaine **deload** est planifiée toutes les 4 semaines (5/3/1) "
                 "pour purger la fatigue. Vise 7-9 h de sommeil ; si la fatigue "
                 "grimpe plusieurs jours, lève le pied avant que l'ACWR ne dépasse "
                 "1,3.")
    return "\n".join(lines)


_HANDLERS = {
    "help": _h_help,
    "today": _h_today,
    "schedule": _h_schedule,
    "rpe": _h_rpe,
    "nutrition": _h_nutrition,
    "strength": _h_strength,
    "run": _h_run,
    "wod": _h_wod,
    "sciatica": _h_sciatica,
    "raid": _h_raid,
    "benchmarks": _h_benchmarks,
    "recovery": _h_recovery,
}

_SUGGESTIONS = {
    "today": ["Quelle allure pour mon footing ?", "C'est quoi une grande semaine ?",
              "Que manger après la séance ?"],
    "schedule": ["Qu'est-ce que je fais aujourd'hui ?", "C'est quoi un jour OFF ?"],
    "rpe": ["Explique-moi le RPE 8", "Comment coter une séance de force ?"],
    "nutrition": ["Combien de protéines par jour ?", "Quels compléments prendre ?",
                  "Créatine : comment ?"],
    "strength": ["Mon objectif au développé couché ?", "C'est quoi le 5/3/1 ?",
                 "Comment progresser aux tractions ?"],
    "run": ["Mes zones de fréquence cardiaque ?", "C'est quoi une séance de seuil ?"],
    "wod": ["Comment marche le chrono ?", "Différence AMRAP / For Time ?"],
    "sciatica": ["Quels mouvements éviter ?", "Alternative au soulevé de terre ?"],
    "raid": ["Combien de semaines avant la sélection ?", "Mes objectifs de force ?"],
    "benchmarks": ["Quand re-tester ?", "Mes objectifs élite ?"],
    "recovery": ["C'est quoi une semaine deload ?", "Comment lire ma readiness ?"],
    "help": ["Qu'est-ce que je fais aujourd'hui ?", "Explique-moi le RPE",
             "Combien de protéines par jour ?"],
    "fallback": ["Qu'est-ce que je fais aujourd'hui ?", "Explique-moi le RPE",
                 "Mon planning de la semaine"],
}


def answer(message: str, context: dict | None = None) -> dict:
    """Réponse du coach à un message en langage naturel.

    `context` (optionnel) peut contenir : profile, today, metrics, weeks_to_goal.
    """
    ctx = dict(context or {})
    ctx["_message"] = message or ""
    topic = detect_topic(message)
    handler = _HANDLERS.get(topic)
    if handler is None:
        prof = _profile_lines(ctx)
        extra = (" Voilà ce que je sais de toi : " + ", ".join(prof) + "."
                 if prof else "")
        reply = ("Je n'ai pas bien saisi la question 🤔. Je suis affûté sur "
                 "l'entraînement (course, force, WOD), la nutrition, le RPE, ton "
                 "planning et la sélection RAID." + extra +
                 " Essaie une des suggestions ci-dessous.")
        topic = "fallback"
    else:
        reply = handler(ctx)
    return {
        "reply": reply,
        "topic": topic,
        "suggestions": _SUGGESTIONS.get(topic, _SUGGESTIONS["fallback"]),
    }
