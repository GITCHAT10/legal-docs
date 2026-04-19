from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from mnos.modules.inn.housekeeping.models import TaskStatus

class HousekeepingTaskBase(BaseModel):
    room_id: int
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    description: Optional[str] = None

class HousekeepingTaskCreate(HousekeepingTaskBase):
    pass

class HousekeepingTaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    assigned_to: Optional[str] = None

class HousekeepingTask(HousekeepingTaskBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
