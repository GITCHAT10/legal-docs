from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional
from .models import ReservationStatus, RoomStatus

class StayBase(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date

class StayCreate(StayBase):
    pass

class Stay(StayBase):
    id: int
    reservation_id: int
    is_active: bool
    trace_id: str

    class Config:
        from_attributes = True

class ReservationBase(BaseModel):
    guest_id: int
    status: ReservationStatus = ReservationStatus.PENDING
    total_amount: float = 0.0
    adults: int = 1
    children: int = 0
    trace_id: str
    tenant_id: str = "default"

class ReservationCreate(ReservationBase):
    stays: List[StayCreate]

class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None

class Reservation(ReservationBase):
    id: int
    stays: List[Stay]
    created_at: datetime

    class Config:
        from_attributes = True

class RoomBase(BaseModel):
    room_number: str
    room_type: str
    status: RoomStatus = RoomStatus.READY
    base_price: float = 0.0
    capacity: int = 2
    trace_id: str
    tenant_id: str = "default"

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
