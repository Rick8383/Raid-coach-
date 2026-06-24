"""Coach Chat — assistant de coaching déterministe (sans LLM externe).

Route une question en langage naturel (FR) vers le bon moteur / la bonne base
de connaissances, personnalise la réponse avec le profil athlète et le contexte
du jour. Offline-friendly, testable, sans dépendance réseau.
"""
from .engine import RPE_SCALE, answer, detect_topic
from .llm import is_enabled as llm_enabled, llm_answer

__all__ = ["answer", "detect_topic", "RPE_SCALE", "llm_answer", "llm_enabled"]
