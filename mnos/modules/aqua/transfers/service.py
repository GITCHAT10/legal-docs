from typing import Optional, List
from sqlalchemy.orm import Session
from mnos.modules.aqua.transfers import models, schemas
from mnos.core.events.dispatcher import event_dispatcher

def create_transfer_request(db: Session, *, request_in: schemas.TransferRequestCreate) -> models.TransferRequest:
    db_obj = models.TransferRequest(**request_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    event_dispatcher.dispatch("transfer_requested", {"transfer_request_id": db_obj.id})
    return db_obj

def update_transfer_status(db: Session, request_id: int, status: models.TransferStatus) -> Optional[models.TransferRequest]:
    db_obj = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
    if not db_obj:
        return None
    db_obj.status = status
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    event_dispatcher.dispatch("transfer_status_updated", {"transfer_request_id": db_obj.id, "status": status})
    return db_obj

def assign_vehicle(db: Session, request_id: int, vehicle_id: int) -> Optional[models.TransferRequest]:
    db_obj = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
    if not db_obj:
        return None
    db_obj.vehicle_id = vehicle_id
    db_obj.status = models.TransferStatus.ASSIGNED
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    event_dispatcher.dispatch("transfer_assigned", {"transfer_request_id": db_obj.id, "vehicle_id": vehicle_id})
    return db_obj
