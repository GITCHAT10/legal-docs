from typing import Optional, List
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from mnos.modules.inn.reservations.models import ReservationStatus, RoomStatus

class RoomBase(BaseModel):
    room_number: str
    room_type: str
    status: RoomStatus = RoomStatus.READY
    base_price: float = 0.0

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int

    class Config:
        from_attributes = True

class StayBase(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date

class StayCreate(StayBase):
    pass

class Stay(StayBase):
    id: int
    reservation_id: int

    class Config:
        from_attributes = True

class ReservationBase(BaseModel):
    guest_id: int
    status: ReservationStatus = ReservationStatus.PENDING
    total_amount: float = 0.0

class ReservationCreate(ReservationBase):
    stays: List[StayCreate]

class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None

class Reservation(ReservationBase):
    id: int
    stays: List[Stay] = []

    class Config:
        from_attributes = True
