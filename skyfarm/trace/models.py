from sqlalchemy import Column, String, DateTime
from skyfarm.database import Base
from datetime import datetime

class TraceRecordModel(Base):
    __tablename__ = "trace_records"
    id = Column(String, primary_key=True, index=True)
    item_id = Column(String)
    action = Column(String)
    actor_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(String)
