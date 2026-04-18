from sqlalchemy import Column, String, Integer, DateTime, JSON
from skyfarm.database import Base
from datetime import datetime

class IntegrationOutboxModel(Base):
    __tablename__ = "integration_outbox"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, index=True)
    event_type = Column(String)
    payload_json = Column(JSON)
    status = Column(String, default="pending") # pending, sent, failed
    attempt_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    idempotency_key = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
