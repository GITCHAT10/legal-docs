from fastapi import FastAPI, Request
from pydantic import BaseModel
import uuid
import json

app = FastAPI(title="MNOS EVENTS")

class EventRequest(BaseModel):
    type: str
    payload: dict

@app.post("/api/core/events/publish")
async def publish(request: EventRequest):
    event_id = f"EVT-{uuid.uuid4()}"
    # In a real implementation, this would push to Redis
    # print(f"Publishing event {event_id}: {request.type}")
    return {
        "status": "success",
        "event_id": event_id
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
