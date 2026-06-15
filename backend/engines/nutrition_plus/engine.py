"""Moteur nutrition : convertisseur macro→grammes, garde-fous, planning compléments."""
from __future__ import annotations

from .data import FOODS_BY_ID, SUPPLEMENTS


def _round5(x: float) -> int:
    return int(round(x / 5) * 5)


def food_portions(target_p: float, target_c: float, target_f: float,
                  protein_id: str = "poulet", carb_id: str = "rizcuit",
                  fat_id: str = "huileolive") -> dict:
    """Traduit une cible macro (g) en grammes d'aliments réels (source au choix)."""
    pf = FOODS_BY_ID.get(protein_id, FOODS_BY_ID["poulet"])
    cf = FOODS_BY_ID.get(carb_id, FOODS_BY_ID["rizcuit"])
    ff = FOODS_BY_ID.get(fat_id, FOODS_BY_ID["huileolive"])

    # glucides d'abord ; la source de glucides apporte aussi un peu de protéines
    g_c = _round5(target_c / cf["c"] * 100) if cf["c"] > 0 else 0
    p_from_c = g_c * cf["p"] / 100
    g_p = _round5(max(0.0, target_p - p_from_c) / pf["p"] * 100) if pf["p"] > 0 else 0
    fat_from = g_p * pf["f"] / 100 + g_c * cf["f"] / 100
    rem_f = max(0.0, target_f - fat_from)
    g_f = _round5(rem_f / ff["f"] * 100) if ff["f"] > 0 else 0

    items = []
    for food, grams in [(pf, g_p), (cf, g_c), (ff, g_f)]:
        if grams <= 0:
            continue
        items.append({
            "id": food["id"], "name": food["name"], "grams": grams,
            "p": round(grams * food["p"] / 100, 1),
            "c": round(grams * food["c"] / 100, 1),
            "f": round(grams * food["f"] / 100, 1),
            "kcal": round(grams * food["kcal"] / 100),
        })
    totals = {
        "p": round(sum(i["p"] for i in items), 1),
        "c": round(sum(i["c"] for i in items), 1),
        "f": round(sum(i["f"] for i in items), 1),
        "kcal": round(sum(i["kcal"] for i in items)),
    }
    return {
        "target": {"p": target_p, "c": target_c, "f": target_f},
        "items": items, "totals": totals,
        "note": "Peser les aliments dans l'état indiqué (cuit/cru). Ajuste ±10% selon ta faim.",
    }


def guardrails(weight_kg: float, calories: int, protein_g: float, fat_g: float,
               body_fat_pct: float | None = None, exercise_kcal: int = 500) -> list[dict]:
    """Alertes hormonales / muscle / RED-S (disponibilité énergétique)."""
    ffm = weight_kg * (1 - (body_fat_pct or 15) / 100)
    out = []

    fat_min = round(0.8 * weight_kg)
    out.append({
        "code": "lipides", "level": "alert" if fat_g < fat_min else "ok",
        "message": (f"Lipides {fat_g:.0f} g < {fat_min} g (0,8 g/kg) : risque de baisse de testostérone."
                    if fat_g < fat_min else f"Lipides OK (≥ {fat_min} g, protection hormonale).")})

    prot_min = round(1.8 * weight_kg)
    out.append({
        "code": "proteines", "level": "alert" if protein_g < prot_min else "ok",
        "message": (f"Protéines {protein_g:.0f} g < {prot_min} g (1,8 g/kg) : risque de perte musculaire en déficit."
                    if protein_g < prot_min else f"Protéines OK (≥ {prot_min} g).")})

    ea = (calories - exercise_kcal) / ffm if ffm else 0
    out.append({
        "code": "red_s", "level": "alert" if ea < 25 else ("warn" if ea < 30 else "ok"),
        "message": (f"Disponibilité énergétique {ea:.0f} kcal/kg FFM < 25 : alerte RED-S "
                    "(hypogonadisme, cortisol ↑). Augmente l'apport et réduis la charge."
                    if ea < 25 else
                    (f"Disponibilité énergétique {ea:.0f} kcal/kg FFM : zone de vigilance."
                     if ea < 30 else f"Disponibilité énergétique OK ({ea:.0f} kcal/kg FFM)."))})
    return out


_SESSION_TO_CONTEXT = {
    "strength": "force", "run": "cardio", "crossfit": "wod",
    "swim": "cardio", "recovery": "toujours", "rest": "toujours", "test": "test",
}
_WHEN_ORDER = ["matin", "pre", "post", "soir", "quotidien"]
_WHEN_LABEL = {"matin": "Matin", "pre": "Avant la séance", "post": "Après la séance",
               "soir": "Soir / pré-sommeil", "quotidien": "Quotidien (peu importe l'heure)"}


def supplement_schedule(session_type: str = "rest") -> dict:
    """Compléments pertinents pour le type de séance, groupés par moment de prise."""
    ctx = _SESSION_TO_CONTEXT.get(session_type, "toujours")
    relevant = [s for s in SUPPLEMENTS if ctx in s["contexts"] or "toujours" in s["contexts"]]
    groups = []
    for when in _WHEN_ORDER:
        items = [{"name": s["name"], "dose": s["dose"], "with": s["with"],
                  "evidence": s["evidence"], "why": s["mechanism"]}
                 for s in relevant if s["when"] == when]
        if items:
            groups.append({"when": when, "label": _WHEN_LABEL[when], "items": items})
    return {"session_type": session_type, "context": ctx, "groups": groups}
