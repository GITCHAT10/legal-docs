import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mnos.core.gateway.middleware.schema_guard import SchemaGuard
import uuid
from datetime import datetime, UTC

app = FastAPI()
app.add_middleware(SchemaGuard)

@app.post("/events/publish")
async def publish_event(event: dict):
    return {"status": "published"}

def create_valid_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "CORE.SYSTEM.BOOT",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "CORE" },
        "actor": { "id": "sys_admin", "role": "ADMIN" },
        "context": {
            "tenant": { "brand": "MNOS", "tin": "123456", "jurisdiction": "MV" }
        },
        "payload": { "status": "UP" },
        "proof": {},
        "metadata": { "schema_version": "1.1" }
    }

@pytest.mark.asyncio
async def test_schema_guard_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        event = create_valid_event()
        response = await ac.post("/events/publish", json=event)
        assert response.status_code == 200
        assert response.json() == {"status": "published"}

@pytest.mark.asyncio
async def test_schema_guard_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        event = create_valid_event()
        event["event_type"] = "invalid"
        response = await ac.post("/events/publish", json=event)
        assert response.status_code == 400
        assert "SCHEMA_GUARD_REJECTION" in response.json()["detail"]

@pytest.mark.asyncio
async def test_schema_guard_non_publish_path():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Should not be intercepted by SchemaGuard
        response = await ac.get("/health")
        # Since we didn't define /health, it should be 404, not 400 from guard
        assert response.status_code == 404
