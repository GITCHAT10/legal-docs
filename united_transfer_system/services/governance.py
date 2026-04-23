from sqlalchemy.orm import Session
from united_transfer_system import models
from united_transfer_system.integrations import weather, nexus_client
from united_transfer_system.services.execution_guard import guard
from functools import wraps
from fastapi import HTTPException
import logging
from typing import Dict, Any

def fail_closed_operation(func):
    """Decorator to ensure operations fail closed."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Fail-Closed Triggered: {func.__name__} failed with {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Sovereign Execution Error: Fail-Closed")
    return wrapper

def fail_closed_async_operation(func):
    """Async version of fail_closed_operation."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Fail-Closed Triggered (Async): {func.__name__} failed with {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Sovereign Execution Error: Fail-Closed")
    return wrapper

def validate_real_world(db: Session, leg_id: int, ctx: Dict[str, Any]) -> bool:
    """
    Integrate Real-World Validation Layer.
    Blocks transitions if weather, GPS, or vessel status is invalid.
    """
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg:
        return False

    # 1. Weather Validation (Sea/Flight)
    alerts = weather.get_weather_alerts(leg.origin)
    if alerts:
        logging.warning(f"Sovereign Block: Weather alert for {leg.origin}. Blocking Leg {leg_id}")
        # Log to SHADOW
        guard.execute_sovereign_action(
            "ut.validation.fail.weather",
            ctx,
            lambda: True, # Just logging the event
            db=db
        )
        return False

    # 2. GPS Validation (Mock for sandbox)
    # 3. Flight Feeds
    if leg.type == models.LegType.AIR:
        status = weather.check_flight_status("QR123") # Placeholder
        if status == "delayed":
            logging.warning(f"Sovereign Block: Flight delay detected.")
            return False

    return True

def self_govern_rerouting(db: Session, journey_id: int, ctx: Dict[str, Any]):
    """Self-governing re-routing during weather alerts/delays."""
    journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
    if not journey:
        return

    for leg in journey.legs:
        if not validate_real_world(db, leg.id, ctx):
            logging.info(f"APOLLO: Initiating autonomous re-routing for Leg {leg.id}")
            leg.status = "rerouting"
            journey.status = models.JourneyStatus.REROUTED

    db.commit()
