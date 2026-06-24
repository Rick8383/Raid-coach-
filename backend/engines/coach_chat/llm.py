"""Coach Chat — couche LLM (API Claude).

Si `ANTHROPIC_API_KEY` est défini, le chat devient un vrai coach généraliste
(sport, entraînement, nutrition, récupération, compléments…) qui répond à
TOUTE question, personnalisé avec le contexte de l'athlète. Sinon, le moteur
déterministe (engine.py) prend le relais. Tout échec réseau/API → repli aussi.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_API_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # rapide et économique pour un chat


def is_enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _system_prompt(context: dict) -> str:
    p = (context or {}).get("profile") or {}
    bits = []
    if p.get("name"):
        bits.append(f"Prénom : {p['name']}")
    if p.get("weight_kg"):
        bits.append(f"poids {p['weight_kg']} kg"
                    + (f" (objectif {p['target_weight_kg']} kg)" if p.get("target_weight_kg") else ""))
    if p.get("vma_kmh"):
        bits.append(f"VMA {p['vma_kmh']} km/h")
    if p.get("fc_max"):
        bits.append(f"FCmax {p['fc_max']} bpm")
    if p.get("main_goal"):
        bits.append(f"objectif : {p['main_goal']}")
    cur = p.get("current") or {}
    if cur:
        forces = ", ".join(f"{k} {v}" for k, v in cur.items())
        bits.append(f"maxes actuels : {forces}")
    injuries = p.get("injuries") or []
    inj = "; ".join(f"{i.get('type','')} {i.get('zone','')}".strip() for i in injuries if isinstance(i, dict))
    today = (context or {}).get("today") or {}
    wk = (context or {}).get("weeks_to_goal")

    profile_txt = " · ".join(bits) if bits else "profil non renseigné"
    return (
        "Tu es le coach personnel expert de cet athlète dans l'app RAID Coach. "
        "Tu maîtrises l'entraînement (course, force/5-3-1, CrossFit/WOD, hybride), "
        "la préparation physique, la nutrition et les compléments (evidence-based), "
        "la récupération, le sommeil, la gestion de blessure et la périodisation. "
        "Réponds à TOUTE question liée au sport, à la santé et à la performance — "
        "même hors de son plan (vélo, boxe, JJB, natation, trail…). "
        "Style : français, tutoiement, concret et actionnable, sans bla-bla ; "
        "utilise des listes courtes quand c'est utile. Donne des chiffres et des "
        "repères pratiques. Reste prudent : pour une douleur préoccupante ou un "
        "sujet médical, recommande un avis professionnel, sans alarmer.\n\n"
        f"Contexte athlète : {profile_txt}."
        + (f" Blessure à gérer : {inj}." if inj else "")
        + (f" Aujourd'hui : {today.get('week_type','')}, "
           f"{'jour de service' if today.get('is_work_day') else 'jour OFF/entraînement'}." if today else "")
        + (f" ~{wk} semaines avant son objectif." if wk else "")
    )


def llm_answer(message: str, context: dict | None = None,
               history: list[dict] | None = None) -> str | None:
    """Réponse du LLM, ou None si désactivé/échec (→ repli déterministe)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = os.environ.get("COACH_MODEL", _DEFAULT_MODEL)

    msgs: list[dict] = []
    for h in (history or [])[-10:]:
        role = "assistant" if h.get("role") in ("assistant", "coach") else "user"
        content = str(h.get("content") or h.get("text") or "").strip()
        if content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "max_tokens": 700,
        "system": _system_prompt(context or {}),
        "messages": msgs,
    }
    req = urllib.request.Request(
        _API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        text = "\n".join(t for t in parts if t).strip()
        return text or None
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError, OSError):
        return None
