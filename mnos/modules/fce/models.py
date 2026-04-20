from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from mnos.core.db.base_class import Base

class FolioStatus(str, enum.Enum):
    OPEN = "open"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"

class ChargeType(str, enum.Enum):
    ROOM = "room"
    TRANSFER = "transfer"
    SERVICE = "service"
    TAX = "tax"
    OTHER = "other"

class Folio(Base):
    id = Column(Integer, primary_key=True, index=True)
    external_reservation_id = Column(String, index=True, nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(FolioStatus), default=FolioStatus.OPEN)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("FolioLine", back_populates="folio")
    payments = relationship("Payment", back_populates="folio")

class FolioLine(Base):
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(Enum(ChargeType), nullable=False)
    base_amount = Column(Float, nullable=False)
    service_charge = Column(Float, default=0.0)
    tgst = Column(Float, default=0.0)
    green_tax = Column(Float, default=0.0)
    amount = Column(Float, nullable=False) # Total amount
    description = Column(String)
    is_reversed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio", back_populates="lines")

class Payment(Base):
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PAID)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio", back_populates="payments")

class Invoice(Base):
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    invoice_number = Column(String, unique=True, index=True)
    total_amount = Column(Float, nullable=False)
    tax_summary = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class LedgerEntry(Base):
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    account_code = Column(String, nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExchangeRateLock(Base):
    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String, nullable=False)
    rate = Column(Float, nullable=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
