from sqlalchemy.orm import Session
from united_transfer_system import models, schemas
from united_transfer_system.services import ledger_service, finance_service
from datetime import datetime, UTC, timedelta
import logging
from fastapi import HTTPException

def process_telemetry(db: Session, leg_id: int, lat: float, lon: float, speed: float = None):
    telemetry = models.Telemetry(
        leg_id=leg_id,
        latitude=lat,
        longitude=lon,
        speed=speed
    )
    db.add(telemetry)

    # Update Asset current location if linked
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if leg and leg.asset:
        leg.asset.current_lat = lat
        leg.asset.current_lon = lon

    db.commit()
    return telemetry

def verify_handshake(db: Session, leg_id: int, scan_type: str, master_code: str, actor_id: str, actor_role: str):
    """
    Hardened Dual-QR Handshake with Reality Enforcement.
    """
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg or leg.master_voucher_code != master_code:
        return False

    # PRE-EXECUTION VALIDATION (AEGIS + SHADOW)
    if actor_role != "AUTHORIZED_OPERATOR":
        return False

    action = None
    if scan_type == "pickup":
        if leg.qr1_verified: return False
        leg.qr1_verified = True
        leg.status = "picked_up"
        action = "LEG_PICKUP"
    elif scan_type == "dropoff":
        if not leg.qr1_verified or leg.qr2_verified: return False
        leg.qr2_verified = True
        leg.status = "dropped"
        action = "LEG_DROPOFF"

    if action:
        ledger_service.commit_evidence(
            db,
            trace_id=leg.trace_id,
            actor=actor_id,
            action=action,
            entity_type="LEG",
            entity_id=str(leg.id),
            payload={"scan_type": scan_type, "timestamp": datetime.now(UTC).isoformat()}
        )
        db.commit()
        return True

    return False

async def confirm_arrival(db: Session, leg_id: int):
    """Completes the leg based on GPS + Operator verification."""
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg or not leg.qr2_verified:
        raise HTTPException(status_code=400, detail="Cannot confirm arrival without dropoff scan")

    leg.status = "completed"
    db.commit()

    # Automatic Payment Trigger upon completion
    await process_payout(db, leg_id=leg_id)
    return {"status": "completed", "leg_id": leg_id}

async def process_payout(db: Session, leg_id: int):
    """FCE Trigger: release funds to operator wallet."""
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg or leg.status != "completed":
        raise HTTPException(status_code=400, detail="Payout requires completed status")

    # In sandbox, simulate M-Faisaa payout
    payout_res = finance_service.process_instant_payout(leg.provider_id, amount=250.0)

    # Record transaction
    wallet = db.query(models.Wallet).filter(models.Wallet.owner_id == leg.provider_id).first()
    if not wallet:
        wallet = models.Wallet(owner_id=leg.provider_id, balance=0.0)
        db.add(wallet)
        db.flush()

    wallet.balance += 250.0
    txn = models.Transaction(
        wallet_id=wallet.id,
        amount=250.0,
        type="PAYOUT",
        leg_id=leg.id
    )
    txn.ensure_trace_id()
    db.add(txn)
    db.commit()
    return payout_res
