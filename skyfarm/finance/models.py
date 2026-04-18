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

class PayoutBatchModel(Base):
    __tablename__ = "payout_batches"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="pending") # pending, approved, paid
    total_amount = Column(Float)
    currency = Column(String, default="MVR")
    created_at = Column(DateTime, default=datetime.utcnow)

class LedgerModel(Base):
    __tablename__ = "ledger_entries"
    id = Column(String, primary_key=True, index=True)
    account_id = Column(String)
    type = Column(String) # debit, credit
    amount = Column(Float)
    reference_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
