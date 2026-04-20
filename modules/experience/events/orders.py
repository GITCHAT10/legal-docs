from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class TicketOrder(Base):
    __tablename__ = "ticket_orders"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    buyer_aegis_id = Column(String, index=True)
    event_id = Column(String, nullable=False, index=True)
    order_status = Column(String, default="PENDING")
    currency = Column(String, default="USD")
    subtotal = Column(Numeric(12, 2), nullable=False)
    service_charge_total = Column(Numeric(12, 2), nullable=False)
    tgst_total = Column(Numeric(12, 2), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)
    wallet_applied_amount = Column(Numeric(12, 2), default=0.0)
    payment_reference = Column(String)
    fce_invoice_id = Column(String)
    trace_id = Column(String, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    order_id = Column(String, ForeignKey("ticket_orders.id"), nullable=False)
    event_id = Column(String, nullable=False, index=True)
    ticket_tier_id = Column(String, nullable=False)
    holder_aegis_id = Column(String, index=True)
    wallet_asset_id = Column(String)
    qr_payload_hash = Column(String)
    ticket_status = Column(String, default="ISSUED")
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    refunded_at = Column(DateTime)
    checked_in_at = Column(DateTime)
    transfer_locked = Column(Boolean, default=False)
    trace_id = Column(String)

class WalletMasterPass(Base):
    __tablename__ = "wallet_master_passes"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    wallet_asset_id = Column(String, nullable=False, index=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    outbound_boarding_ref = Column(String)
    return_boarding_ref = Column(String)
    qr_payload_hash = Column(String)
    pass_status = Column(String, default="ACTIVE")
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
