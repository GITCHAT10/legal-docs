from sqlalchemy import Column, String, Float, DateTime, JSON
from skyfarm.database import Base
import uuid
from datetime import datetime

class SettlementModel(Base):
    __tablename__ = "sxos_settlements"
    id = Column(String, primary_key=True, default=lambda: f"set_{uuid.uuid4().hex[:8]}")
    transaction_id = Column(String, index=True)
    tenant_id = Column(String, index=True)
    amount = Column(Float)
    margin = Column(Float)
    yield_amount = Column(Float)
    distributions = Column(JSON)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
