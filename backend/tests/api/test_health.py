import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Powered-By") == "Resili (built on Scrapling - BSD License)"

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    assert response.json() == {"version": "v1", "docs": "/docs"}
    assert response.headers.get("X-Powered-By") == "Resili (built on Scrapling - BSD License)"

@pytest.mark.asyncio
async def test_404_error_handler(client: AsyncClient):
    # Test a route that doesn't exist to verify the global exception handler for HTTPExceptions
    # Actually wait, StarletteHTTPException for 404 should return Dec-D schema.
    response = await client.get("/non-existent-route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["message"] == "Not Found"

@pytest.mark.asyncio
async def test_validation_error_handler(client: AsyncClient):
    # If there was a route expecting query params, we could trigger 422.
    pass
