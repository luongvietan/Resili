"""
Test configuration and fixtures for the Resili backend.
"""
import asyncio
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# psycopg3 async requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI app."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
