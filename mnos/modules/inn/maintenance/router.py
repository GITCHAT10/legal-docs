from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from mnos.core.api import deps
from mnos.modules.inn.maintenance import schemas, models

router = APIRouter()

@router.post("/", response_model=schemas.MaintenanceTicket)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: schemas.MaintenanceTicketCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = models.MaintenanceTicket(**ticket_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[schemas.MaintenanceTicket])
def read_tickets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.MaintenanceTicket).offset(skip).limit(limit).all()

@router.patch("/{ticket_id}", response_model=schemas.MaintenanceTicket)
def update_ticket(
    ticket_id: int,
    update_in: schemas.MaintenanceTicketUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = db.query(models.MaintenanceTicket).filter(models.MaintenanceTicket.id == ticket_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if update_in.status:
        db_obj.status = update_in.status
        if update_in.status == models.MaintenanceStatus.RESOLVED:
            db_obj.resolved_at = datetime.utcnow()
    if update_in.priority:
        db_obj.priority = update_in.priority
    if update_in.assigned_to:
        db_obj.assigned_to = update_in.assigned_to

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
