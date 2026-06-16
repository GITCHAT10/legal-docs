from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from datetime import datetime
from mnos.core.db.base_class import Base

class FinancialPeriod(Base):
    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(Date, unique=True, index=True, nullable=False)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    closed_by = Column(String)

class InvoiceSequence(Base):
    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String, unique=True, nullable=False)
    last_value = Column(Integer, default=0)
