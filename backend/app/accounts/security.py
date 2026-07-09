import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


class InvalidGoogleTokenError(Exception):
    pass


class InvalidSessionTokenError(Exception):
    pass


@dataclass
class GoogleProfile:
    sub: str
    email: str
    name: str
    picture: str | None


def verify_google_id_token(credential: str) -> GoogleProfile:
    """Verify a Google Identity Services ID token and extract the profile.

    Raises InvalidGoogleTokenError if the token's signature, audience, or
    issuer don't check out.
    """
    try:
        payload = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.google_client_id
        )
    except ValueError as exc:
        raise InvalidGoogleTokenError(str(exc)) from exc

    return GoogleProfile(
        sub=payload["sub"],
        email=payload["email"],
        name=payload.get("name", payload["email"]),
        picture=payload.get("picture"),
    )


def create_session_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.session_max_age_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_session_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidSessionTokenError(str(exc)) from exc
