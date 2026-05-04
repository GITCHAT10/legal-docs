from sqlalchemy import Column, String, Float, DateTime, JSON
from skyfarm.database import Base
from datetime import datetime

class AgriHarvestModel(Base):
    __tablename__ = "agri_harvests"
    id = Column(String, primary_key=True, index=True)
    facility_id = Column(String)
    crop_type = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ProductionBatchModel(Base):
    __tablename__ = "production_batches"
    id = Column(String, primary_key=True, index=True)
    source_ids = Column(JSON) # List of harvest/catch IDs
    status = Column(String, default="created")
    timestamp = Column(DateTime, default=datetime.utcnow)
