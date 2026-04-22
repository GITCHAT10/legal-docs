from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from mnos.modules.inn.laundry.models import LaundryStatus

class LaundryItemBase(BaseModel):
    folio_id: int
    guest_id: int
    status: LaundryStatus = LaundryStatus.PENDING
    description: Optional[str] = None
    item_count: int = 1
    total_price: float = 0.0

class LaundryItemCreate(LaundryItemBase):
    pass

class LaundryItemUpdate(BaseModel):
    status: Optional[LaundryStatus] = None
    total_price: Optional[float] = None

class LaundryItem(LaundryItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
