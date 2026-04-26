from sqlalchemy.orm import Session
from united_transfer_system import models
from datetime import datetime, timedelta, UTC
import json
import hashlib

def calculate_dynamic_threshold(route_density: float, time_window_hours: int) -> int:
    """
    Dynamic threshold calculation for charter consolidation.
    """
    base_threshold = 5 # Standard Gulf Craft 40 efficiency point
    # If high density or narrow window, we can consolidate earlier
    if route_density > 0.8:
        return 3
    return base_threshold

def consolidate_bookings(db: Session):
    """
    Autonomous consolidation with dynamic thresholds.
    """
    now = datetime.now(UTC)
    window = now + timedelta(hours=24)

    pending_legs = db.query(models.Leg).filter(
        models.Leg.status == "scheduled",
        models.Leg.departure_time >= now,
        models.Leg.departure_time <= window,
        models.Leg.type == models.LegType.SEA
    ).all()

    # Group by route (origin-destination)
    routes = {}
    for leg in pending_legs:
        key = f"{leg.origin}->{leg.destination}"
        if key not in routes:
            routes[key] = []
        routes[key].append(leg)

    for route_key, legs in routes.items():
        # Simple density mock: count / capacity
        density = len(legs) / 10.0
        threshold = calculate_dynamic_threshold(density, 24)

        if len(legs) >= threshold:
            route_hash = hashlib.md5(route_key.encode()).hexdigest()[:4]
            manifest = models.CharterManifest(
                trace_id=f"CHARTER-{now.strftime('%Y%m%d%H%M')}-{route_hash}",
                vessel_id="GULF-CRAFT-40-01",
                departure_time=legs[0].departure_time,
                passengers=json.dumps([{"leg_id": l.id, "origin": l.origin} for l in legs]),
                status="draft"
            )
            db.add(manifest)
            db.commit()
            return manifest

    return None

def file_manifest(db: Session, manifest_id: int):
    manifest = db.query(models.CharterManifest).filter(models.CharterManifest.id == manifest_id).first()
    if manifest:
        manifest.filed_at = datetime.now(UTC)
        manifest.status = "filed"
        db.commit()
        return True
    return False
