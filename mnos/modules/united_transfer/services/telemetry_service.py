from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from mnos.modules.united_transfer import models, schemas
from mnos.modules.united_transfer.services import handshake_service
import httpx
import logging

def process_telemetry(db: Session, *, obj_in: schemas.TelemetryCreate, background_tasks: BackgroundTasks):
    db_telemetry = models.Telemetry(
        leg_id=obj_in.leg_id,
        latitude=obj_in.latitude,
        longitude=obj_in.longitude,
        speed=obj_in.speed,
        heading=obj_in.heading
    )
    db.add(db_telemetry)
    db.commit()

    # Logic for Safe Arrival detection
    leg = db.query(models.Leg).filter(models.Leg.id == obj_in.leg_id).first()
    if leg and _is_at_destination(obj_in.latitude, obj_in.longitude, leg.destination):
        background_tasks.add_task(handshake_service.trigger_safe_arrival, db_id=leg.id)
        background_tasks.add_task(dispatch_safe_arrival_webhook, leg_id=leg.id)

    return {"status": "recorded"}

def _is_at_destination(lat, lon, destination):
    # Mock destination check
    return True

async def dispatch_safe_arrival_webhook(leg_id: int):
    """
    SUPER API: Webhooks layer.
    Dispatches 'Safe Arrival' event to authorized partner endpoints.
    """
    webhook_url = "https://partner-api.com/webhooks/safe-arrival" # Placeholder
    payload = {"leg_id": leg_id, "event": "SAFE_ARRIVAL", "timestamp": "now"}

    try:
        async with httpx.AsyncClient() as client:
            # In sandbox, we just log this
            logging.info(f"Dispatching webhook to {webhook_url} for leg {leg_id}")
            # await client.post(webhook_url, json=payload)
    except Exception as e:
        logging.error(f"Failed to dispatch webhook: {e}")
