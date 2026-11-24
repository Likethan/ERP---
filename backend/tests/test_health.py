import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_check(client: AsyncClient):
    """Verify that root /health endpoint returns healthy status and standard envelope."""
    response = await client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert "version" in json_data["data"]
    assert "service" in json_data["data"]


@pytest.mark.asyncio
async def test_api_v1_health_check(client: AsyncClient):
    """Verify that /api/v1/health endpoint returns healthy status and standard envelope."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["service"] == "CampusOS API"
