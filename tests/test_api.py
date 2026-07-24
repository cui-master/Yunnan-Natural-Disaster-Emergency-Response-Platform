import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from app.main import app


class TestAPI:
    @pytest.mark.asyncio
    async def test_root(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
            assert "sse_endpoint" in data

    @pytest.mark.asyncio
    async def test_health(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_list_crawlers(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/crawler/crawlers")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    @pytest.mark.asyncio
    async def test_trigger_crawl(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/crawler/run")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "stats" in data

    @pytest.mark.asyncio
    async def test_list_events(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post("/api/v1/crawler/run")

            response = await client.get("/api/v1/events")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    @pytest.mark.asyncio
    async def test_event_stats(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post("/api/v1/crawler/run")

            response = await client.get("/api/v1/events/stats/summary")
            assert response.status_code == 200
            data = response.json()
            assert "total_events" in data
            assert "by_type" in data
            assert "by_severity" in data
