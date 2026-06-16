from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from mnos.core.db.base_class import Base

class PartnerContract(Base):
    """
    GOVERN Layer: Contract definition.
    Defines profit sharing rules for partners.
    """
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)

    partner_name = Column(String, nullable=False)
    partner_type = Column(String) # VENDOR, INVESTOR, DMC
    share_percentage = Column(Float, nullable=False) # e.g., 30.0 for 30%
    payout_timing = Column(String) # IMMEDIATE, MONTHLY, QUARTERLY

    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_contract_tenant_trace_uc'),)

class RevenueSplit(Base):
    """
    REVENUE Layer: Profit distribution logic.
    Linked to FCE FolioLines.
    """
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)

    line_id = Column(Integer, ForeignKey("folioline.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("partnercontract.id"), nullable=False)

    partner_amount = Column(Float, nullable=False)
    resort_amount = Column(Float, nullable=False)
    tax_allocation = Column(JSON) # Record who paid what portion of TGST/SC

    status = Column(String, default="CALCULATED") # CALCULATED, SETTLED
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("PartnerContract")
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_rev_tenant_trace_uc'),)
