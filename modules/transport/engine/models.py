from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class EventTransportBundle(Base):
    __tablename__ = "event_transport_bundles"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    route_id = Column(String, nullable=False)
    outbound_departure_id = Column(String)
    return_departure_id = Column(String)
    vessel_id = Column(String)
    reserved_capacity = Column(Integer, default=0)
    sold_capacity = Column(Integer, default=0)
    buffer_locked_capacity = Column(Integer, default=0)
    release_policy_json = Column(JSON)
    bundle_status = Column(String, default="ACTIVE")
    trace_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class TransportCapacitySnapshot(Base):
    __tablename__ = "transport_capacity_snapshots"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    route_id = Column(String, nullable=False, index=True)
    departure_id = Column(String, nullable=False, index=True)
    vessel_id = Column(String)
    total_capacity = Column(Integer, nullable=False)
    available_capacity = Column(Integer, nullable=False)
    held_capacity = Column(Integer, default=0)
    sold_capacity = Column(Integer, default=0)
    emergency_buffer_capacity = Column(Integer, default=0)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TransportLink(Base):
    __tablename__ = "transport_links"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    ticket_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    route_id = Column(String)
    outbound_departure_id = Column(String)
    return_departure_id = Column(String)
    manifest_id = Column(String, index=True)
    seat_reference = Column(String)
    boarding_status = Column(String, default="PENDING")
    transport_status = Column(String, default="SCHEDULED")
    linked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trace_id = Column(String)

class Manifest(Base):
    __tablename__ = "manifests"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    route_id = Column(String, nullable=False, index=True)
    departure_id = Column(String, nullable=False, index=True)
    event_id = Column(String, index=True)
    vessel_id = Column(String)
    manifest_status = Column(String, default="OPEN")
    departure_window = Column(String)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
