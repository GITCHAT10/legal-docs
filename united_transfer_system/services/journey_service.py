from sqlalchemy.orm import Session
from united_transfer_system import models, schemas
from united_transfer_system.services import ledger_service
from datetime import datetime, UTC, timedelta
import logging

def process_telemetry(db: Session, leg_id: int, lat: float, lon: float, speed: float = None):
    telemetry = models.Telemetry(
        leg_id=leg_id,
        latitude=lat,
        longitude=lon,
        speed=speed
    )
    db.add(telemetry)
    db.commit()
    return telemetry

def verify_handshake(db: Session, leg_id: int, scan_type: str, master_code: str, actor_id: str, actor_role: str):
    """
    Hardened Dual-QR Handshake:
    - QR1: PICKUP (Driver must scan)
    - QR2: DROPOFF (Driver must scan)
    - Role validation: Only AUTHORIZED_OPERATOR can scan.
    - Mandatory SHADOW commit for every handshake.
    - Expiry: QR expires after 48 hours of leg departure.
    """
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg or leg.master_voucher_code != master_code:
        return False

    # 1. Role Check
    if actor_role != "AUTHORIZED_OPERATOR":
        logging.warning(f"Handshake failed: Unauthorized role {actor_role} for actor {actor_id}")
        return False

    # 2. Expiry Check
    now = datetime.now(UTC)
    if leg.departure_time:
        # Ensure leg.departure_time is also UTC aware if it's not
        dept_time = leg.departure_time
        if dept_time.tzinfo is None:
            dept_time = dept_time.replace(tzinfo=UTC)

        if now > dept_time + timedelta(hours=48):
            logging.warning(f"Handshake failed: QR Code expired for Leg {leg_id}")
            return False

    # 3. State Machine & Reuse Prevention
    action = None
    if scan_type == "pickup":
        if leg.qr1_verified:
            return False # Already picked up
        leg.qr1_verified = True
        leg.status = "picked_up"
        action = "LEG_PICKUP"
    elif scan_type == "dropoff":
        if not leg.qr1_verified or leg.qr2_verified:
            return False # Must be picked up first, and not yet dropped off
        leg.qr2_verified = True
        leg.status = "dropped"
        action = "LEG_DROPOFF"

    if action:
        # 4. Mandatory SHADOW Commit
        ledger_service.commit_evidence(
            db,
            trace_id=leg.trace_id,
            actor=actor_id,
            action=action,
            entity_type="LEG",
            entity_id=str(leg.id),
            payload={
                "scan_type": scan_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "actor_role": actor_role
            }
        )
        db.commit()
        return True

    return False
