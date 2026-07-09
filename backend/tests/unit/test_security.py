import datetime
import uuid
from unittest.mock import patch

import jwt
import pytest

from app.accounts.security import (
    InvalidGoogleTokenError,
    InvalidSessionTokenError,
    create_session_token,
    decode_session_token,
    verify_google_id_token,
)
from app.core.config import settings


def test_session_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_session_token(user_id)
    assert decode_session_token(token) == user_id


def test_decode_session_token_rejects_garbage():
    with pytest.raises(InvalidSessionTokenError):
        decode_session_token("not-a-jwt")


def test_decode_session_token_rejects_expired():
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10),
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3),
    }
    expired = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(InvalidSessionTokenError):
        decode_session_token(expired)


def test_verify_google_id_token_wraps_google_payload():
    fake_payload = {
        "sub": "1234567890",
        "email": "user@example.com",
        "name": "Test User",
        "picture": "https://example.com/pic.jpg",
    }
    with patch(
        "app.accounts.security.google_id_token.verify_oauth2_token", return_value=fake_payload
    ):
        profile = verify_google_id_token("fake-credential")

    assert profile.sub == "1234567890"
    assert profile.email == "user@example.com"
    assert profile.name == "Test User"
    assert profile.picture == "https://example.com/pic.jpg"


def test_verify_google_id_token_raises_on_invalid_token():
    with patch(
        "app.accounts.security.google_id_token.verify_oauth2_token",
        side_effect=ValueError("bad token"),
    ):
        with pytest.raises(InvalidGoogleTokenError):
            verify_google_id_token("garbage")
