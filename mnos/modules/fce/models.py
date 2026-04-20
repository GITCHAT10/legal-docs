from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Numeric, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

class FolioStatus(str, enum.Enum):
    OPEN = "open"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING_RECONCILIATION = "pending_reconciliation"

class ChargeType(str, enum.Enum):
    ROOM = "room"
    TRANSFER = "transfer"
    SERVICE = "service"
    TAX = "tax"
    OTHER = "other"

from mnos.core.db.base_class import Base
class Folio(Base):
    __tablename__ = "folio"
    id = Column(Integer, primary_key=True, index=True)
    external_reservation_id = Column(String, index=True, nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(FolioStatus), default=FolioStatus.OPEN)
    total_amount = Column(Numeric(precision=20, scale=4), default=0.0)
    paid_amount = Column(Numeric(precision=20, scale=4), default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("FolioLine", back_populates="folio")
    invoices = relationship("Invoice", back_populates="folio")
    payments = relationship("Payment", back_populates="folio")

from mnos.core.db.base_class import Base
class FolioLine(Base):
    __tablename__ = "folioline"
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(Enum(ChargeType), nullable=False)
    base_amount = Column(Numeric(precision=20, scale=4), nullable=False)
    service_charge = Column(Numeric(precision=20, scale=4), default=0.0)
    tgst = Column(Numeric(precision=20, scale=4), default=0.0)
    green_tax = Column(Numeric(precision=20, scale=4), default=0.0)
    total_amount = Column(Numeric(precision=20, scale=4), nullable=False)
    description = Column(String)
    is_reversed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio", back_populates="lines")

from mnos.core.db.base_class import Base
class Payment(Base):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Numeric(precision=20, scale=4), nullable=False)
    method = Column(String, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_reference = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio", back_populates="payments")

from mnos.core.db.base_class import Base
class Invoice(Base):
    __tablename__ = "invoice"
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    invoice_number = Column(String, unique=True, index=True)
    total_amount = Column(Numeric(precision=20, scale=4), nullable=False)
    tax_summary = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio", back_populates="invoices")

from mnos.core.db.base_class import Base
class LedgerEntry(Base):
    __tablename__ = "ledgerentry"
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    account_code = Column(String, nullable=False)
    debit = Column(Numeric(precision=20, scale=4), default=0.0)
    credit = Column(Numeric(precision=20, scale=4), default=0.0)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

from mnos.core.db.base_class import Base
class ExchangeRateLock(Base):
    __tablename__ = "exchangeratelock"
    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String, nullable=False)
    rate = Column(Numeric(precision=20, scale=4), nullable=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

from mnos.core.db.base_class import Base
class OutboxEvent(Base):
    __tablename__ = "outboxevent"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    trace_id = Column(String, unique=True, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
