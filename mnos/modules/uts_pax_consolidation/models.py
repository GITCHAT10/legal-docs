from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Float, JSON, Boolean, Numeric, UniqueConstraint
from datetime import datetime, UTC
from mnos.core.db.base_class import Base

class CharterManifest(Base):
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    vessel_id = Column(String, nullable=False)
    departure_time = Column(DateTime, nullable=False)

    passengers = Column(JSON) # List of passenger details for MoT/Coast Guard
    filed_at = Column(DateTime)
    status = Column(String, default="draft") # draft, filed, accepted
