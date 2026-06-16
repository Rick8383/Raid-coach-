"""Coach Chat — assistant de coaching déterministe (sans LLM externe).

Route une question en langage naturel (FR) vers le bon moteur / la bonne base
de connaissances, personnalise la réponse avec le profil athlète et le contexte
du jour. Offline-friendly, testable, sans dépendance réseau.
"""
from .engine import RPE_SCALE, answer, detect_topic

__all__ = ["answer", "detect_topic", "RPE_SCALE"]
