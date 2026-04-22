from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import TransferType, TransferStatus

class VehicleBase(BaseModel):
    name: str
    type: TransferType
    capacity: Optional[int] = None
    license_plate: Optional[str] = None
    trace_id: str
    tenant_id: str = "default"

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TransferRequestBase(BaseModel):
    external_reservation_id: str
    type: TransferType
    pickup_location: Optional[str] = None
    destination: Optional[str] = None
    trace_id: str
    tenant_id: str = "default"
    guest_id: Optional[int] = None

class TransferRequestCreate(TransferRequestBase):
    pass

class TransferRequestUpdate(BaseModel):
    status: Optional[TransferStatus] = None
    vehicle_id: Optional[int] = None
    eta: Optional[datetime] = None

class TransferRequest(TransferRequestBase):
    id: int
    status: TransferStatus
    vehicle_id: Optional[int]
    eta: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
