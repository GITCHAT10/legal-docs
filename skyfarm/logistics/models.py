from sqlalchemy import Column, String, Float, DateTime, JSON
from skyfarm.database import Base
from datetime import datetime

class LogisticsEventModel(Base):
    __tablename__ = "logistics_events"
    id = Column(String, primary_key=True, index=True)
    batch_id = Column(String)
    vessel_id = Column(String, nullable=True)
    origin = Column(String)
    destination = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, default={})
