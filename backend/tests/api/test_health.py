from unittest.mock import MagicMock, patch

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
    pass


def test_sentry_init_called_when_dsn_set():
    """AC 3: Verify sentry_sdk.init() is called when SENTRY_DSN is configured."""
    from app.core.config import Settings

    mock_settings = MagicMock(spec=Settings)
    mock_settings.SENTRY_DSN = "https://fake-key@sentry.io/123456"
    mock_settings.ENVIRONMENT = "production"

    with patch("app.main.settings", mock_settings), \
         patch("app.main._sentry_initialized", False), \
         patch("sentry_sdk.init") as mock_sentry_init:
        from app.main import create_app
        create_app()
        mock_sentry_init.assert_called_once_with(
            dsn="https://fake-key@sentry.io/123456",
            traces_sample_rate=0.1,
            environment="production",
        )


def test_sentry_not_called_when_dsn_not_set():
    """AC 3: Verify sentry_sdk.init() is NOT called when SENTRY_DSN is None."""
    from app.core.config import Settings

    mock_settings = MagicMock(spec=Settings)
    mock_settings.SENTRY_DSN = None
    mock_settings.ENVIRONMENT = "production"

    with patch("app.main.settings", mock_settings), \
         patch("app.main._sentry_initialized", False), \
         patch("sentry_sdk.init") as mock_sentry_init:
        from app.main import create_app
        create_app()
        mock_sentry_init.assert_not_called()
