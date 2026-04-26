from sqlalchemy import Column, Integer, String, DateTime, JSON
from mnos.core.db.base_class import Base, TraceableMixin
from datetime import datetime

class Evidence(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    actor = Column(String)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    before_state = Column(JSON)
    after_state = Column(JSON)
    payload = Column(JSON, nullable=False)
    previous_hash = Column(String, nullable=False)
    payload_digest = Column(String, nullable=False)
    current_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
