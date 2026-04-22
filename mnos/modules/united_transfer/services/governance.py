from sqlalchemy.orm import Session
from mnos.modules.united_transfer import models
from mnos.modules.united_transfer.integrations import weather

def self_govern_rerouting(db: Session, journey_id: int):
    """
    Self-Governing: Manages its own re-routing during weather alerts
    without human intervention.
    """
    journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
    if not journey:
        return

    for leg in journey.legs:
        alerts = weather.get_weather_alerts(leg.origin)
        if alerts:
            print(f"Weather alert detected for {leg.origin}. Initiating autonomous re-routing.")
            leg.status = "rerouting"
            journey.status = models.JourneyStatus.REROUTED

    db.commit()
