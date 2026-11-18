import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["app"] == "SafeHer"
    assert "docs_url" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "SafeHer"
    assert data["version"] == "0.1.0"
    assert data["emergency_fallback_number"] == "112"
    # Rule 5 check: Mock integrations must be truthfully labeled
    assert data["integrations"]["sms"] == "[MOCK]"
    assert data["integrations"]["push"] == "[MOCK]"


@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_security_and_correlation_headers(client: AsyncClient) -> None:
    test_req_id = "test-custom-request-id-12345"
    response = await client.get("/", headers={"X-Request-ID": test_req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == test_req_id
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Process-Time" in response.headers
