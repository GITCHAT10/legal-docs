from sqlalchemy.orm import Session
from united_transfer_system import models
from datetime import datetime, UTC
import logging

def check_weather_alerts():
    """Mock Met Office API call."""
    # Simulation: 10% chance of a Yellow Alert
    import random
    if random.random() < 0.1:
        return {"status": "ALERT", "level": "YELLOW", "region": "MALÉ_ATOLL"}
    return {"status": "CLEAR"}

def autonomous_reroute(db: Session, leg_id: int):
    """
    Handle autonomous re-routing due to weather or delays.
    """
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg:
        return None

    weather = check_weather_alerts()
    if weather["status"] == "ALERT":
        if leg.type == models.LegType.SEA:
            # Re-route Sea to Air if possible
            logging.info(f"Rerouting Leg {leg_id} from SEA to AIR due to weather alert.")
            leg.type = models.LegType.AIR
            leg.status = "rerouted"
            db.commit()
            return leg
    return None

def monitor_delays(db: Session):
    """
    Monitor flight delays and adjust dependent legs.
    """
    # Logic to check flight stats and shift schedule
    pass
