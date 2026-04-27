from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base import Base, TraceableMixin

class FlightStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    LANDED = "landed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"

class FlightMvpSession(Base, TraceableMixin):
    """
    MVP Flight Tracking Session.
    """
    id = Column(Integer, primary_key=True, index=True)
    session_ref = Column(String, unique=True, index=True) # PH-FLT-MVP-001
    booking_id = Column(String, index=True, nullable=False)
    journey_id = Column(Integer, index=True)

    flight_number = Column(String(10), nullable=False)
    origin_iata = Column(String(3), nullable=False)
    destination_iata = Column(String(3), default="MLE")

    scheduled_departure_utc = Column(DateTime(timezone=True), nullable=False)
    scheduled_arrival_utc = Column(DateTime(timezone=True), nullable=False)
    estimated_arrival_utc = Column(DateTime(timezone=True))

    flight_status = Column(Enum(FlightStatus), default=FlightStatus.SCHEDULED)
    delay_minutes = Column(Integer, default=0)

    ut_ticket_ref = Column(String)
    ut_auto_adjust_enabled = Column(Boolean, default=True)

    guest_count = Column(Integer, nullable=False)
    gccc_mode = Column(Boolean, default=False)

    last_data_refresh = Column(DateTime(timezone=True))

    events = relationship("FlightMvpEvent", back_populates="session")

class FlightMvpEvent(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    flight_session_id = Column(Integer, ForeignKey("flightmvpsession.id"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String) # status_change, delay_detected, landed, ut_adjusted
    event_data = Column(String) # JSON string
    guest_notified = Column(Boolean, default=False)

    session = relationship("FlightMvpSession", back_populates="events")
