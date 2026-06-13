"""Intégration Garmin Connect — OAuth 1.0a côté serveur (Garmin Health API).

Activation : définir les variables d'environnement
  GARMIN_CONSUMER_KEY, GARMIN_CONSUMER_SECRET   (programme développeur Garmin)
  GARMIN_REDIRECT_URL = https://<api>/garmin/callback
Sans ces clés, le module reste inactif (`is_configured()` → False) et l'app
bascule sur la saisie manuelle / Apple Santé.

Flux : request token → l'utilisateur autorise sur connect.garmin.com → callback
(oauth_token + oauth_verifier) → access token → appels Wellness API signés OAuth1.
Les données quotidiennes (FC repos, HRV, sommeil) sont écrites dans daily_metrics
et alimentent la boucle adaptative (suivi + plan), sans toucher aux générateurs.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

try:  # dépendance optionnelle : l'app tourne sans (intégration simplement inactive)
    from requests_oauthlib import OAuth1Session
except ImportError:  # pragma: no cover
    OAuth1Session = None  # type: ignore

# Endpoints Garmin (surchargables par env pour tests / évolutions d'API)
REQUEST_TOKEN_URL = os.environ.get(
    "GARMIN_REQUEST_TOKEN_URL", "https://connectapi.garmin.com/oauth-service/oauth/request_token")
AUTHORIZE_URL = os.environ.get(
    "GARMIN_AUTHORIZE_URL", "https://connect.garmin.com/oauthConfirm")
ACCESS_TOKEN_URL = os.environ.get(
    "GARMIN_ACCESS_TOKEN_URL", "https://connectapi.garmin.com/oauth-service/oauth/access_token")
WELLNESS_BASE = os.environ.get(
    "GARMIN_WELLNESS_BASE", "https://apis.garmin.com/wellness-api/rest")


def _key() -> str | None:
    return os.environ.get("GARMIN_CONSUMER_KEY")


def _secret() -> str | None:
    return os.environ.get("GARMIN_CONSUMER_SECRET")


def _redirect() -> str:
    return os.environ.get("GARMIN_REDIRECT_URL", "http://localhost:8000/garmin/callback")


def is_configured() -> bool:
    """Vrai si les clés Garmin et la lib OAuth sont présentes."""
    return bool(_key() and _secret() and OAuth1Session is not None)


# ---------- Stockage des tokens (1 ligne / athlète) ----------
class GarminTokenStore:
    def __init__(self, db) -> None:
        self.db = db

    def get(self, athlete_id: int) -> dict | None:
        rows = self.db.query("SELECT * FROM garmin_tokens WHERE athlete_id = ?", (athlete_id,))
        return rows[0] if rows else None

    def save_request_token(self, athlete_id: int, token: str, secret: str) -> None:
        self.db.execute(
            """INSERT INTO garmin_tokens (athlete_id, request_token, request_token_secret)
               VALUES (?,?,?)
               ON CONFLICT(athlete_id) DO UPDATE SET
                 request_token=excluded.request_token,
                 request_token_secret=excluded.request_token_secret""",
            (athlete_id, token, secret))

    def save_access_token(self, athlete_id: int, token: str, secret: str) -> None:
        self.db.execute(
            """UPDATE garmin_tokens SET access_token=?, access_token_secret=?,
               connected_at=?, request_token=NULL, request_token_secret=NULL
               WHERE athlete_id=?""",
            (token, secret, datetime.now(timezone.utc).isoformat(), athlete_id))

    def disconnect(self, athlete_id: int) -> None:
        self.db.execute("DELETE FROM garmin_tokens WHERE athlete_id = ?", (athlete_id,))

    def is_connected(self, athlete_id: int) -> bool:
        row = self.get(athlete_id)
        return bool(row and row.get("access_token"))


# ---------- Flux OAuth ----------
def start_oauth() -> tuple[str, str, str]:
    """Retourne (authorize_url, request_token, request_token_secret)."""
    if not is_configured():
        raise RuntimeError("garmin_not_configured")
    oauth = OAuth1Session(_key(), client_secret=_secret(), callback_uri=_redirect())
    fetched = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    token = fetched.get("oauth_token")
    secret = fetched.get("oauth_token_secret")
    authorize_url = f"{AUTHORIZE_URL}?oauth_token={token}"
    return authorize_url, token, secret


def complete_oauth(request_token: str, request_token_secret: str,
                   oauth_verifier: str) -> tuple[str, str]:
    """Échange le request token vérifié contre un access token."""
    if not is_configured():
        raise RuntimeError("garmin_not_configured")
    oauth = OAuth1Session(
        _key(), client_secret=_secret(),
        resource_owner_key=request_token, resource_owner_secret=request_token_secret,
        verifier=oauth_verifier)
    tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    return tokens["oauth_token"], tokens["oauth_token_secret"]


def _session(access_token: str, access_secret: str):
    return OAuth1Session(_key(), client_secret=_secret(),
                         resource_owner_key=access_token, resource_owner_secret=access_secret)


def fetch_wellness(access_token: str, access_secret: str, day: str) -> dict:
    """Récupère résumé quotidien, sommeil et HRV pour une date (YYYY-MM-DD)."""
    start = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
    end = start + 86400
    params = {"uploadStartTimeInSeconds": start, "uploadEndTimeInSeconds": end}
    s = _session(access_token, access_secret)

    def _get(path: str) -> list:
        r = s.get(f"{WELLNESS_BASE}/{path}", params=params, timeout=20)
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else [data]

    return {
        "dailies": _get("dailies"),
        "sleeps": _get("sleeps"),
        "hrv": _get("hrv"),
    }


def map_to_metrics(wellness: dict) -> dict:
    """Transforme les résumés Garmin en métriques daily_metrics (fonction pure)."""
    out: dict[str, float] = {}
    dailies = wellness.get("dailies") or []
    sleeps = wellness.get("sleeps") or []
    hrv = wellness.get("hrv") or []

    if dailies:
        rhr = dailies[-1].get("restingHeartRateInBeatsPerMinute")
        if rhr:
            out["resting_hr"] = int(rhr)
    if sleeps:
        dur = sleeps[-1].get("durationInSeconds")
        if dur:
            hours = round(dur / 3600, 1)
            out["sleep_hours"] = hours
            out["sleep_quality"] = min(100, round(40 + min(1.0, hours / 8) * 60))
    if hrv:
        # selon l'appareil : lastNightAvg (ms) ou weeklyAvg
        avg = hrv[-1].get("lastNightAvg") or hrv[-1].get("weeklyAvg")
        if avg:
            out["hrv"] = round(float(avg), 1)
    return out
