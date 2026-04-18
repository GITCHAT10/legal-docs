from sqlalchemy import Column, String, Float, DateTime
from skyfarm.database import Base
from datetime import datetime

class FinanceEventModel(Base):
    __tablename__ = "finance_events"
    id = Column(String, primary_key=True, index=True)
    type = Column(String)
    amount = Column(Float)
    currency = Column(String, default="USD")
    reference_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
