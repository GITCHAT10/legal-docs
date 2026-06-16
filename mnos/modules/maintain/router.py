from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.maintain import schemas, models, service, enums

router = APIRouter()

@router.post("/", response_model=schemas.MaintenanceTicket)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: schemas.MaintenanceTicketCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.create_ticket(db, **ticket_in.dict(), actor=current_user.email)

@router.get("/", response_model=List[schemas.MaintenanceTicket])
def read_tickets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.MaintenanceTicket).offset(skip).limit(limit).all()

@router.put("/{ticket_id}", response_model=schemas.MaintenanceTicket)
def update_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    ticket_in: schemas.MaintenanceTicketUpdate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    ticket = db.query(models.MaintenanceTicket).filter(models.MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket_in.status:
        return service.update_ticket_status(db, ticket_id, ticket_in.status, actor=current_user.email)

    # Handle other updates
    update_data = ticket_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket
