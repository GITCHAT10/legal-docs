from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from mnos.modules.aqua.transfers.models import TransferType, TransferStatus

class VehicleBase(BaseModel):
    name: str
    type: TransferType
    capacity: Optional[int] = None
    license_plate: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int

    class Config:
        from_attributes = True

class TransferRequestBase(BaseModel):
    reservation_id: int
    type: TransferType
    status: TransferStatus = TransferStatus.PENDING
    pickup_time: Optional[datetime] = None
    eta: Optional[datetime] = None
    pickup_location: Optional[str] = None
    destination: Optional[str] = None
    vehicle_id: Optional[int] = None

class TransferRequestCreate(TransferRequestBase):
    pass

class TransferRequestUpdate(BaseModel):
    status: Optional[TransferStatus] = None
    eta: Optional[datetime] = None
    vehicle_id: Optional[int] = None

class TransferRequest(TransferRequestBase):
    id: int

    class Config:
        from_attributes = True

class ManifestCreate(BaseModel):
    transfer_request_id: int
    guest_id: int

class Manifest(ManifestCreate):
    id: int

    class Config:
        from_attributes = True
