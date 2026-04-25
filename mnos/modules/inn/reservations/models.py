from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Float, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
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
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    created_by = Column(String, default="SYSTEM")

    room_number = Column(String, index=True, nullable=False)
    room_type = Column(String, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.READY)
    base_price = Column(Float, default=0.0)
    capacity = Column(Integer, default=2)

    __table_args__ = (UniqueConstraint('tenant_id', 'room_number', name='_room_tenant_number_uc'),
                      UniqueConstraint('tenant_id', 'trace_id', name='_room_tenant_trace_uc'))

class Reservation(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    created_by = Column(String, default="SYSTEM")

    guest_id = Column(Integer, ForeignKey("guest.id"), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)

    guest = relationship("Guest")
    stays = relationship("Stay", back_populates="reservation")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_res_tenant_trace_uc'),)

class Stay(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    created_by = Column(String, default="SYSTEM")

    reservation_id = Column(Integer, ForeignKey("reservation.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    reservation = relationship("Reservation", back_populates="stays")
    room = relationship("Room")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_stay_tenant_trace_uc'),)
