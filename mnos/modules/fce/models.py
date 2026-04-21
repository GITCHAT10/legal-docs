from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, DateTime, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from mnos.core.db.base_class import Base

class FolioStatus(str, enum.Enum):
    OPEN = "open"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"
    REVERSED = "reversed"

class ChargeType(str, enum.Enum):
    ROOM = "room"
    TRANSFER = "transfer"
    SERVICE = "service"
    TAX = "tax"
    OTHER = "other"

class Folio(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    external_reservation_id = Column(String, index=True, nullable=False)
    status = Column(Enum(FolioStatus), default=FolioStatus.OPEN)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")

    lines = relationship("FolioLine", back_populates="folio")
    transactions = relationship("FolioTransaction", back_populates="folio")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_folio_tenant_trace_uc'),)

class FolioLine(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    type = Column(Enum(ChargeType), nullable=False)
    base_amount = Column(Float, nullable=False)
    service_charge = Column(Float, default=0.0)
    tgst = Column(Float, default=0.0)
    green_tax = Column(Float, default=0.0)
    amount = Column(Float, nullable=False) # Total authoritative amount
    description = Column(String)
    is_reversed = Column(Boolean, default=False)
    reversal_of_entry_id = Column(Integer, ForeignKey("folioline.id")) # Explicit Reversal Doctrine

    folio = relationship("Folio", back_populates="lines")
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_folioline_tenant_trace_uc'),)

class FolioTransaction(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=False) # cash, credit_card, etc
    status = Column(Enum(TransactionStatus), default=TransactionStatus.POSTED)
    reversal_of_transaction_id = Column(Integer, ForeignKey("foliotransaction.id"))

    folio = relationship("Folio", back_populates="transactions")
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_foliotransaction_tenant_trace_uc'),)
