from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class EventOrganizer(Base):
    __tablename__ = "event_organizers"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    legal_name = Column(String)
    organizer_type = Column(String)
    aegis_subject_id = Column(String, index=True)
    kyb_status = Column(String)
    commission_profile_id = Column(String)
    payout_config_json = Column(JSON)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Venue(Base):
    __tablename__ = "venues"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    venue_type = Column(String)
    island = Column(String)
    atoll = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    capacity = Column(Integer)
    transport_required = Column(Boolean, default=False)
    metadata_json = Column(JSON)

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    organizer_id = Column(String, ForeignKey("event_organizers.id"), nullable=False)
    venue_id = Column(String, ForeignKey("venues.id"), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True)
    description = Column(Text)
    category = Column(String)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    timezone = Column(String, default="Indian/Maldives")
    visibility = Column(String, default="PUBLIC")
    publication_status = Column(String, default="DRAFT")
    base_capacity = Column(Integer)
    effective_capacity = Column(Integer)
    transport_mode = Column(String)
    transport_link_required = Column(Boolean, default=False)
    currency = Column(String, default="USD")
    tax_config_mira_json = Column(JSON)
    status = Column(String, default="ACTIVE")
    trace_id = Column(String)
    version = Column(Integer, default=1)
    created_by = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class TicketTier(Base):
    __tablename__ = "ticket_tiers"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    base_price = Column(Numeric(12, 2), nullable=False)
    inventory_limit = Column(Integer)
    per_user_limit = Column(Integer)
    sale_start_at = Column(DateTime)
    sale_end_at = Column(DateTime)
    status = Column(String, default="ACTIVE")
