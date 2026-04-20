from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from mnos.modules.inn.maintenance.models import MaintenanceStatus, MaintenancePriority

class MaintenanceTicketBase(BaseModel):
    room_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: MaintenanceStatus = MaintenanceStatus.OPEN
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    assigned_to: Optional[str] = None

class MaintenanceTicketCreate(MaintenanceTicketBase):
    pass

class MaintenanceTicketUpdate(BaseModel):
    status: Optional[MaintenanceStatus] = None
    priority: Optional[MaintenancePriority] = None
    assigned_to: Optional[str] = None

class MaintenanceTicket(MaintenanceTicketBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
