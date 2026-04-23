from sqlalchemy.orm import Session
from united_transfer_system import models, schemas
from mnos.modules.shadow import service as shadow_service
from united_transfer_system.services.execution_guard import guard
from united_transfer_system.integrations.nexus_client import nexus_client
import uuid
import logging
from typing import Dict, Any

def create_journey(db: Session, *, obj_in: schemas.JourneyCreate, ctx: Dict[str, Any]) -> models.Journey:
    """Atomic Journey Creation via ExecutionGuard."""

    def _execute(db: Session):
        db_journey = models.Journey(
            tenant_id=obj_in.tenant_id,
            trace_id=obj_in.trace_id,
            aegis_id=ctx.get("aegis_id"),
            device_id=ctx.get("device_id"),
            external_reference=obj_in.external_reference,
            status=models.JourneyStatus.CREATED
        )
        db.add(db_journey)
        db.flush()

        for leg_in in obj_in.legs:
            db_leg = models.Leg(
                journey_id=db_journey.id,
                trace_id=f"LEG-{uuid.uuid4().hex[:8]}",
                type=leg_in.type,
                origin=leg_in.origin,
                destination=leg_in.destination,
                departure_time=leg_in.departure_time,
                master_voucher_code=f"QR-{uuid.uuid4().hex[:10].upper()}"
            )
            db.add(db_leg)

        db.commit()
        db.refresh(db_journey)
        return db_journey

    return guard.execute_sovereign_action("ut.journey.create", ctx, _execute, db=db)

def update_journey_status(db: Session, journey_id: int, status: models.JourneyStatus, ctx: Dict[str, Any]) -> models.Journey:
    """Strict State Machine Enforcement."""

    def _execute(db: Session):
        journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
        if not journey:
            raise ValueError("Journey not found")

        # State Machine Logic
        valid_transitions = {
            models.JourneyStatus.CREATED: [models.JourneyStatus.CONFIRMED, models.JourneyStatus.CANCELLED],
            models.JourneyStatus.CONFIRMED: [models.JourneyStatus.DISPATCHED, models.JourneyStatus.CANCELLED],
            models.JourneyStatus.DISPATCHED: [models.JourneyStatus.PICKED_UP],
            models.JourneyStatus.PICKED_UP: [models.JourneyStatus.IN_TRANSIT],
            models.JourneyStatus.IN_TRANSIT: [models.JourneyStatus.DROPPED],
            models.JourneyStatus.DROPPED: [models.JourneyStatus.COMPLETED],
            models.JourneyStatus.COMPLETED: [models.JourneyStatus.PAID]
        }

        if status not in valid_transitions.get(journey.status, []):
            raise ValueError(f"Invalid transition from {journey.status} to {status}")

        journey.status = status
        db.commit()
        db.refresh(journey)
        return journey

    return guard.execute_sovereign_action("ut.journey.update", ctx, _execute, db=db)

def verify_handshake(db: Session, leg_id: int, qr_type: str, scan_data: str, ctx: Dict[str, Any]):
    """Enforce Dual-QR Handshake."""

    def _execute(db: Session):
        leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
        if not leg:
            raise ValueError("Leg not found")

        if leg.master_voucher_code != scan_data:
            raise ValueError("Invalid QR Handshake")

        if qr_type == "QR1": # PICKUP
            leg.qr1_verified = True
            update_journey_status(db, leg.journey_id, models.JourneyStatus.PICKED_UP, ctx)
        elif qr_type == "QR2": # DROP
            if not leg.qr1_verified:
                raise ValueError("Cannot verify DROP before PICKUP (QR1 missing)")
            leg.qr2_verified = True
            update_journey_status(db, leg.journey_id, models.JourneyStatus.DROPPED, ctx)

        db.commit()
        return {"status": "verified", "type": qr_type}

    return guard.execute_sovereign_action(f"ut.{qr_type.lower()}.verify", ctx, _execute, db=db)

async def release_payment(db: Session, journey_id: int, ctx: Dict[str, Any]):
    """Payment Gate: QR1 + QR2 + COMPLETED."""

    async def _execute_async(db: Session):
        journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
        if not journey or journey.status != models.JourneyStatus.COMPLETED:
            raise ValueError("Payment Blocked: Journey not completed")

        for leg in journey.legs:
            if not (leg.qr1_verified and leg.qr2_verified):
                raise ValueError(f"Payment Blocked: Leg {leg.id} missing QR verification")

        # FCE Integration: Finalize Invoice before Payment
        invoice = await nexus_client.finalize_invoice(journey.id, ctx.get("trace_id"))
        if not invoice:
            raise ValueError("FCE Failure: Could not finalize invoice")

        # Execute Payout
        payout_success = await nexus_client.release_payout(journey.id, ctx.get("trace_id"))
        if payout_success:
            update_journey_status(db, journey.id, models.JourneyStatus.PAID, ctx)
            return {"status": "paid", "invoice_id": invoice.get("id")}

        raise ValueError("Payment Release Failed at Gateway")

    return await guard.execute_sovereign_action_async("ut.payment.release", ctx, _execute_async, db=db)

def get_availability(db: Session, query: schemas.AvailabilityQuery):
    return [
        {"type": "land", "provider": "Taxi-01", "price": 150.0},
        {"type": "air", "provider": "IAS-ATR72", "price": 2500.0},
        {"type": "sea", "provider": "Speedboat-X", "price": 500.0}
    ]
