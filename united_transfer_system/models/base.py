from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Float, JSON, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base import Base, TraceableMixin

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

class Partner(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tier = Column(Enum(PartnerTier), default=PartnerTier.STABILIZING)
    trust_score = Column(Float, default=0.5)
    max_daily_volume = Column(Integer, default=10)

    legs = relationship("Leg", back_populates="partner")

class Asset(Base, TraceableMixin):
    """Base model for Vessels and Vehicles."""
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String) # vessel, vehicle
    capacity = Column(Integer)
    status = Column(String, default="available")
    current_lat = Column(Float)
    current_lon = Column(Float)

    legs = relationship("Leg", back_populates="asset")

class Journey(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    external_reference = Column(String, index=True) # TA/DMC ref
    status = Column(Enum(JourneyStatus), default=JourneyStatus.CREATED)

    legs = relationship("Leg", back_populates="journey")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_journey_tenant_trace_uc'),)

class Leg(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journey.id"), nullable=False)
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    type = Column(Enum(LegType), nullable=False)
    asset_id = Column(Integer, ForeignKey("asset.id"))
    provider_id = Column(String) # Driver/Vessel ID
    partner_id = Column(Integer, ForeignKey("partner.id"))

    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_time = Column(DateTime(timezone=True))
    arrival_time = Column(DateTime(timezone=True))

    status = Column(String, default="scheduled")
    qr1_verified = Column(Boolean, default=False) # Passenger Scan
    qr2_verified = Column(Boolean, default=False) # Operator Scan
    master_voucher_code = Column(String, index=True)

    journey = relationship("Journey", back_populates="legs")
    partner = relationship("Partner", back_populates="legs")
    asset = relationship("Asset", back_populates="legs")
    telemetry = relationship("Telemetry", back_populates="leg")

class Telemetry(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    leg_id = Column(Integer, ForeignKey("leg.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)
    heading = Column(Float)

    leg = relationship("Leg", back_populates="telemetry")

class Wallet(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, unique=True, index=True) # Driver/Vessel ID
    balance = Column(Numeric(12, 2), default=0.0)
    currency = Column(String, default="MVR")

    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallet.id"), nullable=False)
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String) # PAYOUT, WITHDRAWAL
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    leg_id = Column(Integer, ForeignKey("leg.id"))

    wallet = relationship("Wallet", back_populates="transactions")

class CharterManifest(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(String, nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)

    passengers = Column(JSON) # List of passenger details for MoT/Coast Guard
    filed_at = Column(DateTime(timezone=True))
    status = Column(String, default="draft") # draft, filed, accepted
