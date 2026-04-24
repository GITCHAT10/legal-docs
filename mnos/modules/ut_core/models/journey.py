from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Float, JSON, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base_class import Base

class LegType(str, enum.Enum):
    AIR = "air"
    LAND = "land"
    SEA = "sea"

class JourneyStatus(str, enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DROPPED = "dropped"
    COMPLETED = "completed"
    PAID = "paid"
    CANCELLED = "cancelled"
    REROUTED = "rerouted"

class Journey(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False) # MANDATORY: trace_id + aegis_id + device_id + ts
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    external_reference = Column(String, index=True) # TA/DMC ref
    status = Column(Enum(JourneyStatus), default=JourneyStatus.CREATED)

    legs = relationship("Leg", back_populates="journey")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_journey_tenant_trace_uc'),)

class Leg(Base):
    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journey.id"), nullable=False)
    trace_id = Column(String, index=True, nullable=False) # MANDATORY
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    type = Column(Enum(LegType), nullable=False)
    provider_id = Column(String) # Driver/Vessel ID

    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)

    status = Column(String, default="scheduled")
    qr1_verified = Column(Boolean, default=False) # PICKUP
    qr2_verified = Column(Boolean, default=False) # DROP
    master_voucher_code = Column(String, index=True) # The QR code base

    journey = relationship("Journey", back_populates="legs")
    telemetry = relationship("Telemetry", back_populates="leg")

class Telemetry(Base):
    id = Column(Integer, primary_key=True, index=True)
    leg_id = Column(Integer, ForeignKey("leg.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)
    heading = Column(Float)

    leg = relationship("Leg", back_populates="telemetry")
