from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
import enum
from mnos.core.db.base_class import Base

class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class RoomStatus(str, enum.Enum):
    READY = "ready"
    DIRTY = "dirty"
    MAINTENANCE = "maintenance"
    OCCUPIED = "occupied"
    OUT_OF_ORDER = "ooo"

class Room(Base):
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True, nullable=False)
    room_type = Column(String, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.READY)
    base_price = Column(Float, default=0.0)
    capacity = Column(Integer, default=2)

class Reservation(Base):
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guest.id"), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)

    guest = relationship("Guest")
    stays = relationship("Stay", back_populates="reservation")

class Stay(Base):
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservation.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True) # For room changes

    reservation = relationship("Reservation", back_populates="stays")
    room = relationship("Room")
