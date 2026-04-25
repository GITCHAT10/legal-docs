from sqlalchemy.orm import Session
from mnos.modules.uts_pax_consolidation import models
from mnos.modules.ut_core.models import journey as core_models
from datetime import datetime, UTC
import uuid

def check_and_consolidate(db: Session):
    """
    Autonomously consolidate fragmented bookings into high-capacity charters
    when volume thresholds are met.
    """
    # Logic to find pending legs on the same route/time
    pending_legs = db.query(core_models.Leg).filter(core_models.Leg.status == "scheduled").all()

    # Simple consolidation by destination
    route_groups = {}
    for leg in pending_legs:
        route_groups.setdefault(leg.destination, []).append(leg)

    consolidated = []
    for dest, legs in route_groups.items():
        if len(legs) >= 3: # Lowered threshold for sandbox demonstration
            manifest = models.CharterManifest(
                trace_id=f"CHARTER-{uuid.uuid4().hex[:8]}",
                vessel_id="GULF-CRAFT-40-POWER",
                departure_time=datetime.now(UTC),
                passengers=[{"leg_id": l.id, "origin": l.origin} for l in legs],
                status="filed"
            )
            db.add(manifest)
            for l in legs:
                l.status = "consolidated"
            consolidated.append(manifest)

    db.commit()
    return consolidated
