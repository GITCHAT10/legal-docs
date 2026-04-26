from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, DateTime, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base_class import Base, TraceableMixin

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

class Folio(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String, default="SYSTEM")

    external_reservation_id = Column(String, index=True, nullable=False)
    status = Column(Enum(FolioStatus), default=FolioStatus.OPEN)
    finalized_by = Column(String)
    finalized_at = Column(DateTime)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")

    # MIRA Specifics
    mira_gst_amount = Column(Float, default=0.0)
    mira_green_tax_amount = Column(Float, default=0.0)
    mira_receipt_number = Column(String, index=True)
    qr_authorization_id = Column(String)

    lines = relationship("FolioLine", back_populates="folio")
    transactions = relationship("FolioTransaction", back_populates="folio")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_folio_tenant_trace_uc'),)

class FolioLine(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    version = Column(Integer, default=1, nullable=False)
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

class FolioTransaction(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String, default="SYSTEM")

    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=False) # cash, credit_card, etc
    status = Column(Enum(TransactionStatus), default=TransactionStatus.POSTED)
    reversal_of_transaction_id = Column(Integer, ForeignKey("foliotransaction.id"))

    folio = relationship("Folio", back_populates="transactions")
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_foliotransaction_tenant_trace_uc'),)

class Invoice(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")

    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    invoice_number = Column(String, unique=True, index=True)
    total_amount = Column(Float)

class QRAuthorizationRequest(Base, TraceableMixin):
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    status = Column(String, default="PENDING") # PENDING, AUTHORIZED, REJECTED
    intent_payload = Column(JSON)
    intent_signature_hash = Column(String)
    auth_payload = Column(JSON)
    auth_signature_hash = Column(String)
