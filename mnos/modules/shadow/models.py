from sqlalchemy import Column, Integer, String, DateTime, JSON
from mnos.core.db.base_class import Base
from datetime import datetime

class Evidence(Base):
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    previous_hash = Column(String, nullable=False)
    payload_digest = Column(String, nullable=False)
    current_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
