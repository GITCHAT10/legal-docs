from sqlalchemy import Column, Integer, String, Enum, Float, Boolean, DateTime
from datetime import datetime, UTC
from mnos.core.db.base_class import Base
import enum

class VesselType(str, enum.Enum):
    SAFARI = "safari"
    SPEEDBOAT = "speedboat"
    DHONI = "dhoni"
    YACHT = "yacht"

class Vessel(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(Enum(VesselType))
    capacity = Column(Integer)
    license_number = Column(String, unique=True)
    is_active = Column(Boolean, default=True)

class SafariActivity(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # e.g. "Sunset Cruise", "Night Fishing"
    description = Column(String)
    duration_minutes = Column(Integer)
    price_base = Column(Float)
