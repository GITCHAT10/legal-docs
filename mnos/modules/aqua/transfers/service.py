from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from mnos.modules.aqua.transfers import models
from mnos.modules.inn.reservations.models import Reservation
from mnos.modules.shadow import service as shadow_service
import uuid

def assign_vehicle(db: Session, request_id: int, vehicle_id: int, actor: str = "SYSTEM") -> models.TransferRequest:
    try:
        request = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
        if not request:
            raise ValueError("Transfer request not found")

        if request.status == models.TransferStatus.CANCELLED:
            raise ValueError("Cannot assign vehicle to a cancelled transfer")

        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise ValueError("Vehicle not found")

        if vehicle.type != request.type:
            raise ValueError(f"Vehicle type {vehicle.type} does not match request type {request.type}")

        before_state = {"vehicle_id": request.vehicle_id, "status": request.status}

        request.vehicle_id = vehicle_id
        request.status = models.TransferStatus.ASSIGNED

        trace_id = f"ASSIGN-{uuid.uuid4().hex[:8]}"

        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "ASSIGN_VEHICLE",
            "entity_type": "TRANSFER_REQUEST",
            "entity_id": request.id,
            "before_state": before_state,
            "after_state": {"vehicle_id": vehicle_id, "status": request.status}
        })

        db.commit()
        db.refresh(request)
        return request
    except Exception:
        db.rollback()
        raise

def update_manifest(db: Session, request_id: int, guest_ids: List[int], actor: str = "SYSTEM") -> List[models.Manifest]:
    try:
        request = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
        if not request:
            raise ValueError("Transfer request not found")

        # Get old manifest for audit
        old_manifest = db.query(models.Manifest).filter(models.Manifest.transfer_request_id == request_id).all()
        before_state = {"guest_ids": [m.guest_id for m in old_manifest]}

        # Clear existing manifest
        db.query(models.Manifest).filter(models.Manifest.transfer_request_id == request_id).delete()

        new_manifest = []
        for gid in guest_ids:
            m = models.Manifest(transfer_request_id=request_id, guest_id=gid)
            db.add(m)
            new_manifest.append(m)

        trace_id = f"MANIFEST-{uuid.uuid4().hex[:8]}"

        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "UPDATE_MANIFEST",
            "entity_type": "MANIFEST",
            "entity_id": request_id,
            "before_state": before_state,
            "after_state": {"guest_ids": guest_ids}
        })

        db.commit()
        return new_manifest
    except Exception:
        db.rollback()
        raise

def handle_reservation_cancellation(db: Session, reservation_id: int, actor: str = "SYSTEM"):
    transfers = db.query(models.TransferRequest).filter(
        models.TransferRequest.reservation_id == reservation_id,
        models.TransferRequest.status != models.TransferStatus.COMPLETED
    ).all()
    for t in transfers:
        trace_id = f"CANCEL-T-{uuid.uuid4().hex[:8]}"
        before_state = {"status": t.status}
        t.status = models.TransferStatus.CANCELLED

        db.flush()
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "CANCEL_TRANSFER",
            "entity_type": "TRANSFER_REQUEST",
            "entity_id": t.id,
            "before_state": before_state,
            "after_state": {"status": t.status}
        })
    db.commit()
