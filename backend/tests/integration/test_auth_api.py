import pytest

from app.accounts import security

pytestmark = pytest.mark.anyio


def _fake_profile(sub="google-sub-1", email="user@example.com", name="Test User"):
    return security.GoogleProfile(sub=sub, email=email, name=name, picture=None)


async def test_google_sign_in_creates_user_and_sets_cookie(async_client, monkeypatch):
    monkeypatch.setattr(security, "verify_google_id_token", lambda credential: _fake_profile())

    resp = await async_client.post("/api/v1/internal/auth/google", json={"credential": "fake"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "user@example.com"
    assert body["name"] == "Test User"

    from app.core.config import settings

    assert settings.session_cookie_name in resp.cookies


async def test_google_sign_in_upserts_existing_user_by_sub(async_client, monkeypatch):
    monkeypatch.setattr(security, "verify_google_id_token", lambda credential: _fake_profile())
    first = await async_client.post("/api/v1/internal/auth/google", json={"credential": "fake"})

    monkeypatch.setattr(
        security, "verify_google_id_token", lambda credential: _fake_profile(name="Updated Name")
    )
    second = await async_client.post("/api/v1/internal/auth/google", json={"credential": "fake"})

    assert first.json()["id"] == second.json()["id"]
    assert second.json()["name"] == "Updated Name"


async def test_google_sign_in_rejects_invalid_token(async_client, monkeypatch):
    def _raise(credential):
        raise security.InvalidGoogleTokenError("bad token")

    monkeypatch.setattr(security, "verify_google_id_token", _raise)

    resp = await async_client.post("/api/v1/internal/auth/google", json={"credential": "fake"})
    assert resp.status_code == 401


async def test_me_requires_authentication(async_client):
    resp = await async_client.get("/api/v1/internal/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(authenticated_client):
    resp = await authenticated_client.get("/api/v1/internal/auth/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(authenticated_client.current_user.id)


async def test_logout_clears_session(authenticated_client):
    from app.core.config import settings

    resp = await authenticated_client.post("/api/v1/internal/auth/logout")
    assert resp.status_code == 204

    set_cookie_header = resp.headers.get("set-cookie", "")
    assert settings.session_cookie_name in set_cookie_header
    assert "Max-Age=0" in set_cookie_header

    # httpx's test client doesn't auto-apply Set-Cookie expiry against a
    # manually-injected cookie the way a real browser would — remove it
    # ourselves to simulate that, then confirm the session is really gone.
    authenticated_client.cookies.delete(settings.session_cookie_name)
    me_resp = await authenticated_client.get("/api/v1/internal/auth/me")
    assert me_resp.status_code == 401
