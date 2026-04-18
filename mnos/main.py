from fastapi import FastAPI, HTTPException, Request
from .security import verify_signature, SECRET_KEY
import logging

app = FastAPI(title="MNOS Gateway Mock")

# Simple audit log and replay protection
audit_log = []
seen_events = set()

@app.post("/integration/v1/entities")
async def receive_entity(request: Request):
    payload = await request.json()
    if not verify_signature(payload, SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_id = payload.get("event_id")
    if event_id in seen_events:
        return {"status": "duplicate", "message": "Event already processed"}

    seen_events.add(event_id)
    audit_log.append(payload)
    return {"status": "success", "message": "Entity received"}

@app.post("/integration/v1/events/{category}")
async def receive_event(category: str, request: Request):
    payload = await request.json()
    if not verify_signature(payload, SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_id = payload.get("event_id")
    if event_id in seen_events:
        return {"status": "duplicate", "message": "Event already processed"}

    seen_events.add(event_id)
    audit_log.append(payload)
    return {"status": "success", "message": f"Event {category} received"}

@app.post("/integration/v1/trace/records")
async def receive_trace(request: Request):
    payload = await request.json()
    if not verify_signature(payload, SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_id = payload.get("event_id")
    if event_id in seen_events:
        return {"status": "duplicate", "message": "Event already processed"}

    seen_events.add(event_id)
    audit_log.append(payload)
    return {"status": "success", "message": "Trace record received"}

@app.get("/mnos/v1/policies/skyfarm")
async def get_policies():
    return {
        "export_rules": "v1.0",
        "quality_thresholds": {"min_grade": "A"},
        "reporting_requirements": "daily"
    }

@app.get("/health")
async def health():
    return {"status": "up"}
