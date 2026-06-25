"""Integration tests for API."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, lifespan, repo

@pytest.fixture(autouse=True)
async def setup_repo():
    # Запускаем lifespan вручную, чтобы repo инициализировался
    async with lifespan(app) as _:
        yield

@pytest.mark.asyncio
async def test_extract_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/extract", json={"text": "Steve Jobs founded Apple."})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entities"]) >= 2
    assert data["graph_id"] is not None

@pytest.mark.asyncio
async def test_extract_empty_text():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/extract", json={"text": ""})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Text must not be empty"