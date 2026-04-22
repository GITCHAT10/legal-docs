from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from mnos.core.db.base import Base

class FolioStatus(str, enum.Enum):
    OPEN = "OPEN"
    FINALIZED = "FINALIZED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    PENDING_RECONCILIATION = "PENDING_RECONCILIATION"

class Folio(Base):
    __tablename__ = "fce_folios"

    id = Column(Integer, primary_key=True, index=True)
    external_reservation_id = Column(String, index=True, nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(FolioStatus), default=FolioStatus.OPEN)
    total_amount = Column(Numeric(precision=20, scale=2), default=0)
    paid_amount = Column(Numeric(precision=20, scale=2), default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    lines = relationship("FolioLine", back_populates="folio")
    payments = relationship("Payment", back_populates="folio")

class FolioLine(Base):
    __tablename__ = "fce_folio_lines"

    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("fce_folios.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)
    base_amount = Column(Numeric(precision=20, scale=2), nullable=False)
    service_charge = Column(Numeric(precision=20, scale=2), default=0)
    tgst = Column(Numeric(precision=20, scale=2), default=0)
    green_tax = Column(Numeric(precision=20, scale=2), default=0)
    total_amount = Column(Numeric(precision=20, scale=2), nullable=False)
    description = Column(String)

    folio = relationship("Folio", back_populates="lines")

class Payment(Base):
    __tablename__ = "fce_payments"

    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("fce_folios.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Numeric(precision=20, scale=2), nullable=False)
    method = Column(String, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    folio = relationship("Folio", back_populates="payments")

class LedgerEntry(Base):
    __tablename__ = "fce_ledger"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    account_code = Column(String, nullable=False)
    debit = Column(Numeric(precision=20, scale=2), default=0)
    credit = Column(Numeric(precision=20, scale=2), default=0)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class OutboxEvent(Base):
    __tablename__ = "fce_outbox"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(String, nullable=False) # JSON
    trace_id = Column(String, unique=True, index=True, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
