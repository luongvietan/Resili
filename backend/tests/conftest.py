"""
Test configuration and fixtures for the Resili backend.
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI app."""
    # Import app here to avoid issues when DATABASE_URL is not set
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
