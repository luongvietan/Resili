"""Tests for Story 2.2: User Login & JWT Authentication."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM

_REGISTER_URL = "/api/v1/auth/register"
_LOGIN_URL = "/api/v1/auth/login"
_ME_URL = "/api/v1/auth/me"

_VALID_EMAIL = "logintest@example.com"
_VALID_PASSWORD = "securepass123"


async def _register_and_login(client: AsyncClient) -> str:
    """Helper: register a user and return a valid access token."""
    await client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})
    resp = await client.post(_LOGIN_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})
    return resp.json()["access_token"]


# — AC1: Valid credentials → 200 with token ————————————————————————————


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})

    response = await client.post(_LOGIN_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


# — AC2: Wrong password → 401 INVALID_CREDENTIALS ————————————————————


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})

    response = await client.post(_LOGIN_URL, json={"email": _VALID_EMAIL, "password": "wrongpassword"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    response = await client.post(
        _LOGIN_URL, json={"email": "nobody@example.com", "password": _VALID_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_same_error_for_wrong_password_and_unknown_email(client: AsyncClient):
    """AC2: Prevent email enumeration — same response body for both failure modes."""
    await client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})

    wrong_pw_resp = await client.post(
        _LOGIN_URL, json={"email": _VALID_EMAIL, "password": "wrongpass"}
    )
    unknown_resp = await client.post(
        _LOGIN_URL, json={"email": "ghost@example.com", "password": _VALID_PASSWORD}
    )

    assert wrong_pw_resp.status_code == unknown_resp.status_code == 401
    assert (
        wrong_pw_resp.json()["error"]["code"]
        == unknown_resp.json()["error"]["code"]
        == "INVALID_CREDENTIALS"
    )
    assert (
        wrong_pw_resp.json()["error"]["message"]
        == unknown_resp.json()["error"]["message"]
    )


# — AC3: JWT claims — user_id (UUID) + exp, expires 24h ———————————————


@pytest.mark.asyncio
async def test_jwt_contains_user_id_and_exp(client: AsyncClient):
    reg_resp = await client.post(
        _REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD}
    )
    user_id = reg_resp.json()["id"]

    login_resp = await client.post(
        _LOGIN_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD}
    )
    token = login_resp.json()["access_token"]

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["user_id"] == user_id
    assert "exp" in payload
    # No extra PII (email, tier, etc.)
    assert "email" not in payload
    assert "tier" not in payload


@pytest.mark.asyncio
async def test_jwt_expires_in_24_hours(client: AsyncClient):
    await client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})

    before = datetime.now(timezone.utc)
    login_resp = await client.post(
        _LOGIN_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD}
    )
    after = datetime.now(timezone.utc)

    token = login_resp.json()["access_token"]
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected_min = before + timedelta(hours=23, minutes=59)
    expected_max = after + timedelta(hours=24, minutes=1)

    assert expected_min <= exp <= expected_max


# — AC4: No token → 401 MISSING_AUTH_TOKEN ——————————————————————————


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.get(_ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_AUTH_TOKEN"


# — AC5: Expired token → 401 TOKEN_EXPIRED ——————————————————————————


@pytest.mark.asyncio
async def test_protected_endpoint_with_expired_token(client: AsyncClient):
    expired_payload = {
        "user_id": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    response = await client.get(_ME_URL, headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


# — AC4+5: Invalid token → 401 INVALID_TOKEN ————————————————————————


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    response = await client.get(_ME_URL, headers={"Authorization": "Bearer notavalidtoken"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


# — AC1+AC4: /me returns user when authenticated ————————————————————


@pytest.mark.asyncio
async def test_me_returns_user_with_valid_token(client: AsyncClient):
    reg_resp = await client.post(
        _REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD}
    )
    user_id = reg_resp.json()["id"]
    token = await _register_and_login(client)

    response = await client.get(_ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == _VALID_EMAIL
    assert "password_hash" not in data
