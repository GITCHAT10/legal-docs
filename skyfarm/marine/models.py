from sqlalchemy import Column, String, Float, DateTime
from skyfarm.database import Base
from datetime import datetime

class CatchLogModel(Base):
    __tablename__ = "marine_catch_logs"
    id = Column(String, primary_key=True, index=True)
    vessel_id = Column(String)
    species = Column(String)
    weight = Column(Float)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="logged")
