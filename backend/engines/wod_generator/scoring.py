"""Score d'un WOD + commentaire HONNÊTE de performance.

Principe : pas de félicitations automatiques. On compare le résultat aux
tentatives précédentes (même format, et à défaut même type de score) et on dit
les choses telles qu'elles sont — un time cap non atteint est un échec à
nommer, une régression est une régression. Le but est un retour exploitable,
pas de la motivation creuse.
"""
from __future__ import annotations


def fmt_time(sec: float | int | None) -> str:
    s = max(0, int(sec or 0))
    return f"{s // 60:02d}:{s % 60:02d}"


def rounds_reps(result: dict) -> tuple[int, int]:
    """(tours COMPLETS, reps faites dans le tour EN COURS). Convention CrossFit
    « 2+22 » : deux tours terminés puis 22 répétitions du troisième. Les vieux
    enregistrements n'ont qu'un total de reps → (0, total)."""
    return int(result.get("rounds") or 0), int(result.get("reps") or 0)


def score_label(result: dict) -> str:
    """Libellé court affiché dans l'agenda/l'historique."""
    mode = result.get("mode")
    if mode == "for_time":
        base = fmt_time(result.get("time_sec"))
        return f"{base} (cap)" if result.get("capped") else base
    rounds, reps = rounds_reps(result)
    tours = f"{rounds} tour" + ("s" if rounds > 1 else "")
    if rounds and reps:
        return f"{tours} + {reps} reps"
    if rounds:
        return tours
    if reps:
        return f"{reps} reps"
    return "score non saisi"


def _pct(a: float, b: float) -> float:
    return 0.0 if b == 0 else round(100 * (a - b) / b, 1)


def assess(result: dict, history: list[dict] | None = None) -> dict:
    """Commentaire honnête. `history` = résultats passés, du plus ancien au plus
    récent, chacun {mode, time_sec, reps, capped, cap_sec, format_key?}.
    Renvoie {verdict, comment, reference, delta_pct}."""
    history = [h for h in (history or []) if isinstance(h, dict)]
    mode = result.get("mode")
    fmt_key = result.get("format_key")

    # Référence : même format en priorité, sinon même type de score.
    same_fmt = [h for h in history if fmt_key and h.get("format_key") == fmt_key]
    same_mode = [h for h in history if h.get("mode") == mode]
    pool = same_fmt or same_mode
    ref_scope = "même format" if same_fmt else "même type de score"

    if mode == "for_time":
        capped = bool(result.get("capped"))
        t = int(result.get("time_sec") or 0)
        cap = int(result.get("cap_sec") or 0)
        if capped or (cap and t >= cap):
            return {
                "verdict": "non terminé",
                "comment": ("Time cap atteint : le WOD n'est pas fini. Ce n'est pas un "
                            "échec grave, c'est une info — la prochaine fois, réduis les "
                            "charges ou scale les mouvements pour finir dans le cap."),
                "reference": None, "delta_pct": None,
            }
        finished = [h for h in pool
                    if not h.get("capped") and int(h.get("time_sec") or 0) > 0]
        if not finished:
            return {
                "verdict": "référence posée",
                "comment": (f"Terminé en {fmt_time(t)}, sous le cap. Première référence "
                            "sur ce format : c'est ce chrono qu'il faudra battre."),
                "reference": None, "delta_pct": None,
            }
        best = min(int(h["time_sec"]) for h in finished)
        d = _pct(t, best)                    # négatif = plus rapide
        if t < best:
            return {
                "verdict": "record",
                "comment": (f"{fmt_time(t)} : meilleur temps sur ce format "
                            f"({abs(d):.0f} % plus rapide que ton {fmt_time(best)}). "
                            "Progression réelle, pas un hasard si la charge suit."),
                "reference": fmt_time(best), "delta_pct": d,
            }
        if d <= 5:
            return {
                "verdict": "stable",
                "comment": (f"{fmt_time(t)} contre {fmt_time(best)} au mieux : "
                            "équivalent, à la marge de bruit près. Pas de progression "
                            "visible sur ce format — vise le chrono la prochaine fois."),
                "reference": fmt_time(best), "delta_pct": d,
            }
        return {
            "verdict": "en retrait",
            "comment": (f"{fmt_time(t)}, soit {d:.0f} % plus lent que ton meilleur "
                        f"({fmt_time(best)}). À regarder honnêtement : fatigue, sommeil, "
                        "ou rythme de départ trop rapide ?"),
            "reference": fmt_time(best), "delta_pct": d,
        }

    # AMRAP / RFT / EMOM… : score = tours complets, puis reps du tour en cours.
    # On classe comme en compétition : d'abord les tours, les reps départagent.
    mine = rounds_reps(result)
    label = score_label(result)
    scored = [(h, rounds_reps(h)) for h in pool]
    scored = [(h, k) for h, k in scored if k != (0, 0)]
    if mine == (0, 0):
        return {
            "verdict": "score manquant",
            "comment": "Aucun score saisi : sans chiffre, impossible de suivre la progression.",
            "reference": None, "delta_pct": None,
        }
    if not scored:
        return {
            "verdict": "référence posée",
            "comment": (f"{label}. Première référence sur ce format ({ref_scope}) : "
                        "objectif, faire mieux la prochaine fois."),
            "reference": None, "delta_pct": None,
        }
    best_h, best = max(scored, key=lambda x: x[1])
    best_label = score_label(best_h)
    # Écart chiffré seulement quand c'est comparable (mêmes tours, ou aucun tour
    # de part et d'autre) — sinon un % mélangerait tours et reps.
    d = _pct(mine[1], best[1]) if mine[0] == best[0] and best[1] else None
    if mine > best:
        extra = f" (+{d:.0f} %)" if d else ""
        return {
            "verdict": "record",
            "comment": (f"{label} : nouveau record sur ce format, devant {best_label}"
                        f"{extra}. Le moteur suit."),
            "reference": best_label, "delta_pct": d,
        }
    if mine == best or (d is not None and d >= -5):
        return {
            "verdict": "stable",
            "comment": (f"{label} contre {best_label} au mieux : au même niveau. "
                        "Stagnation sur ce format — il faudra pousser le volume "
                        "ou l'intensité pour débloquer."),
            "reference": best_label, "delta_pct": d,
        }
    gap = f", {abs(d):.0f} % sous" if d else ", sous"
    return {
        "verdict": "en retrait",
        "comment": (f"{label}{gap} ton meilleur ({best_label}). Si ce n'est pas un "
                    "jour de fatigue assumé, revois le pacing : partir trop vite "
                    "coûte cher sur ce format."),
        "reference": best_label, "delta_pct": d,
    }
