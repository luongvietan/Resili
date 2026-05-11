import pytest
from httpx import AsyncClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db_engine):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "free"
    assert "id" in data
    assert "created_at" in data
    assert "password_hash" not in data

    # Verify credit_balances was created
    with db_engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM credit_balances WHERE user_id = :uid"), 
            {"uid": data["id"]}
        ).fetchone()
        assert result is not None
        assert result.credits_used == 0
        assert result.monthly_limit == 1000
        assert result.tier == "free"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "securepass123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "differentpass123"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test2@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test3@example.com"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_email_case_insensitive(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "CaseSensitive@Example.COM", "password": "securepass123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "casesensitive@example.com", "password": "anotherpass123"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"
