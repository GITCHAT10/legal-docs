from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Numeric, JSON, Date
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base import Base, TraceableMixin

class CrewRole(str, enum.Enum):
    CAPTAIN = "captain"
    ENGINEER = "engineer"
    DECKHAND = "deckhand"
    STEWARD = "steward"
    RELIEF = "relief"

class CrewStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    STANDBY = "standby"
    SICK = "sick"

class CrewMember(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    role = Column(Enum(CrewRole), nullable=False)
    license_number = Column(String, unique=True)
    license_expiry = Column(Date, nullable=False)
    phone_mv = Column(String) # +960...
    pdpa_consent = Column(Boolean, default=False)
    status = Column(Enum(CrewStatus), default=CrewStatus.AVAILABLE)

class CrewShift(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    crew_id = Column(Integer, ForeignKey("crewmember.id"))
    vessel_id = Column(Integer) # Linked to UT Asset ID
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=False)
    attendance_status = Column(String, default="pending") # pending, checked_in, checked_out

class FuelLog(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, nullable=False)
    trip_id = Column(Integer)
    log_type = Column(String) # refuel, consumption
    liters = Column(Numeric(10, 2), nullable=False)
    cost_mvr = Column(Numeric(12, 2))
    location_atoll = Column(String, nullable=False)
    logged_by = Column(Integer, ForeignKey("crewmember.id"))
    anomaly_flag = Column(Boolean, default=False)

class MaintenanceSchedule(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, nullable=False)
    maintenance_type = Column(String, nullable=False) # service_100h, annual
    next_due = Column(DateTime(timezone=True), nullable=False)
    auto_block_dispatch = Column(Boolean, default=True)

class DispatchAssignment(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    ut_trip_id = Column(Integer, nullable=False)
    vessel_id = Column(Integer, nullable=False)
    captain_id = Column(Integer, ForeignKey("crewmember.id"))
    status = Column(String, default="pending") # confirmed, boarding, in_transit, completed
    priority_score = Column(Numeric(4, 2))
