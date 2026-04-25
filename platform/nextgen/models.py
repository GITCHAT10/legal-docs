from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, Boolean, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class PredictiveDispatchJob(Base):
    __tablename__ = "predictive_dispatch_jobs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, index=True)
    event_id = Column(String, index=True)
    route_id = Column(String)
    departure_window = Column(String)
    dispatch_type = Column(String)
    confidence_score = Column(Float)
    policy_basis_json = Column(JSON)
    status = Column(String, default="PENDING")
    trace_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class GhostBookingHold(Base):
    __tablename__ = "ghost_booking_holds"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, index=True)
    event_id = Column(String, index=True)
    transport_reservation_id = Column(String)
    hold_reason = Column(String)
    confidence_score = Column(Float)
    expires_at = Column(DateTime)
    status = Column(String, default="HELD")
    trace_id = Column(String)

class BiometricGateEvent(Base):
    __tablename__ = "biometric_gate_events"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, index=True)
    gate_id = Column(String, index=True)
    verification_mode = Column(String)
    device_id = Column(String)
    decision = Column(String)
    fallback_used = Column(Boolean, default=False)
    trace_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SpatialPulse(Base):
    __tablename__ = "spatial_pulses"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    event_id = Column(String, index=True)
    venue_id = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)
    pulse_strength = Column(Float)
    occupancy_hint = Column(Integer)
    vibe_score = Column(Float)
    reachability_score = Column(Float)
    weather_hint = Column(String)
    boat_eta_hint = Column(String)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PolicyBufferLock(Base):
    __tablename__ = "policy_buffer_locks"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    event_id = Column(String, index=True)
    route_id = Column(String, index=True)
    locked_percentage = Column(Numeric(5, 2))
    locked_capacity = Column(Integer)
    release_at = Column(DateTime)
    release_policy_json = Column(JSON)
    status = Column(String, default="LOCKED")
