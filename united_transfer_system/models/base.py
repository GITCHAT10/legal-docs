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

class PartnerTier(str, enum.Enum):
    ELITE = "elite"
    HARDENED = "hardened"
    STABILIZING = "stabilizing"
    RESTRICTED = "restricted"

class Partner(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tier = Column(Enum(PartnerTier), default=PartnerTier.STABILIZING)
    trust_score = Column(Float, default=0.5)
    max_daily_volume = Column(Integer, default=10)

    legs = relationship("Leg", back_populates="partner")

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

    type = Column(Enum(LegType), nullable=False)
    provider_id = Column(String) # Driver/Vessel ID
    partner_id = Column(Integer, ForeignKey("partner.id"))

    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)

    status = Column(String, default="scheduled")
    qr1_verified = Column(Boolean, default=False) # PICKUP
    qr2_verified = Column(Boolean, default=False) # DROP
    master_voucher_code = Column(String, index=True) # The QR code base

    journey = relationship("Journey", back_populates="legs")
    partner = relationship("Partner", back_populates="legs")
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

class Wallet(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, unique=True, index=True) # Driver/Vessel ID
    balance = Column(Numeric(12, 2), default=0.0)
    currency = Column(String, default="MVR")

    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(Base):
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallet.id"), nullable=False)
    trace_id = Column(String, index=True, nullable=False) # MANDATORY

    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String) # PAYOUT, WITHDRAWAL
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    leg_id = Column(Integer, ForeignKey("leg.id"))

    wallet = relationship("Wallet", back_populates="transactions")

class CharterManifest(Base):
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    vessel_id = Column(String, nullable=False)
    departure_time = Column(DateTime, nullable=False)

    passengers = Column(JSON) # List of passenger details for MoT/Coast Guard
    filed_at = Column(DateTime)
    status = Column(String, default="draft") # draft, filed, accepted
