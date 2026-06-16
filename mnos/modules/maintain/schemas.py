from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .enums import TicketStatus, TicketPriority, TicketSeverity

class MaintenanceTicketBase(BaseModel):
    room_id: int
    title: str
    description: Optional[str] = None
    priority: TicketPriority = TicketPriority.P3
    severity: TicketSeverity = TicketSeverity.MEDIUM

class MaintenanceTicketCreate(MaintenanceTicketBase):
    pass

class MaintenanceTicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    priority: Optional[TicketPriority] = None
    severity: Optional[TicketSeverity] = None

class MaintenanceTicket(MaintenanceTicketBase):
    id: int
    status: TicketStatus
    assigned_to: Optional[str] = None
    is_blocking: bool
    sla_deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
