from typing import List, Optional, Any
from sqlalchemy.orm import Session
from mnos.modules.aqua.transfers import models, schemas
from mnos.modules.shadow import service as shadow_service
import uuid

def create_vehicle(db: Session, *, vehicle_in: schemas.VehicleCreate, actor: str = "SYSTEM") -> models.Vehicle:
    try:
        db_obj = models.Vehicle(
            tenant_id=vehicle_in.tenant_id,
            trace_id=vehicle_in.trace_id,
            name=vehicle_in.name,
            type=vehicle_in.type,
            capacity=vehicle_in.capacity,
            license_plate=vehicle_in.license_plate,
            created_by=actor
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except Exception:
        db.rollback()
        raise

def create_transfer_request(db: Session, *, request_in: schemas.TransferRequestCreate, actor: str = "SYSTEM") -> models.TransferRequest:
    try:
        db_obj = models.TransferRequest(
            tenant_id=request_in.tenant_id,
            trace_id=request_in.trace_id,
            external_reservation_id=request_in.external_reservation_id,
            type=request_in.type,
            status=models.TransferStatus.PENDING,
            pickup_location=request_in.pickup_location,
            destination=request_in.destination,
            created_by=actor
        )
        db.add(db_obj)
        db.flush()

        shadow_service.commit_evidence(db, request_in.trace_id, {
            "actor": actor, "action": "CREATE_TRANSFER", "entity_type": "TRANSFER_REQUEST", "entity_id": db_obj.id,
            "after_state": {"status": db_obj.status, "type": db_obj.type}
        })

        db.commit()
        db.refresh(db_obj)
        return db_obj
    except Exception:
        db.rollback()
        raise

def assign_vehicle(db: Session, request_id: int, vehicle_id: int, actor: str = "SYSTEM") -> models.TransferRequest:
    try:
        request = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
        if not request: raise ValueError("Transfer request not found")

        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not vehicle: raise ValueError("Vehicle not found")

        before_state = {"vehicle_id": request.vehicle_id, "status": request.status}
        request.vehicle_id = vehicle_id
        request.status = models.TransferStatus.ASSIGNED

        trace_id = f"ASSIGN-{uuid.uuid4().hex[:8]}"
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "ASSIGN_VEHICLE", "entity_type": "TRANSFER_REQUEST", "entity_id": request.id,
            "before_state": before_state, "after_state": {"vehicle_id": vehicle_id, "status": request.status}
        })

        db.commit()
        db.refresh(request)
        return request
    except Exception:
        db.rollback()
        raise

def update_transfer_status(db: Session, request_id: int, status: models.TransferStatus, actor: str = "SYSTEM") -> models.TransferRequest:
    try:
        request = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
        if not request: raise ValueError("Transfer request not found")

        before_state = {"status": request.status}
        request.status = status

        trace_id = f"TRANS-STATUS-{uuid.uuid4().hex[:8]}"
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "UPDATE_TRANSFER_STATUS", "entity_type": "TRANSFER_REQUEST", "entity_id": request.id,
            "before_state": before_state, "after_state": {"status": status}
        })

        db.commit()
        db.refresh(request)
        return request
    except Exception:
        db.rollback()
        raise

def handle_reservation_cancellation(db: Session, reservation_id: int, actor: str = "SYSTEM"):
    # This might need external_reservation_id if we want to be consistent
    # For now, let's stick to the internal ID or find by external
    transfers = db.query(models.TransferRequest).filter(
        models.TransferRequest.external_reservation_id == str(reservation_id),
        models.TransferRequest.status != models.TransferStatus.COMPLETED
    ).all()
    for t in transfers:
        update_transfer_status(db, request_id=t.id, status=models.TransferStatus.CANCELLED, actor=actor)
