import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Set testing environment before app initialization
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters-long"

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
