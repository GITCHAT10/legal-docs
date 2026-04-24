from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Float, JSON, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, UTC
from mnos.core.db.base_class import Base

class PartnerTier(str, enum.Enum):
    ELITE = "elite"
    HARDENED = "hardened"
    STABILIZING = "stabilizing"
    RESTRICTED = "restricted"

class Partner(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tier = Column(Enum(PartnerTier), default=PartnerTier.STABILIZING)
    trust_score = Column(Float, default=0.5)
    max_daily_volume = Column(Integer, default=10)

class Wallet(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, unique=True, index=True) # Driver/Vessel ID
    balance = Column(Numeric(12, 2), default=0.0)
    currency = Column(String, default="MVR")

    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(Base):
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallet.id"), nullable=False)
    trace_id = Column(String, index=True, nullable=False) # MANDATORY
    aegis_id = Column(String, index=True)
    device_id = Column(String, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String) # PAYOUT, WITHDRAWAL
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    leg_id = Column(Integer, ForeignKey("leg.id")) # Note: This creates a cross-file relationship potential issue, but in the same module it's usually fine or use string ref

    wallet = relationship("Wallet", back_populates="transactions")
