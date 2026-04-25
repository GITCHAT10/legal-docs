from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Numeric, ARRAY, CheckConstraint, UniqueConstraint, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from mnos.core.db.base_class import Base
import uuid

class Trace(Base):
    __tablename__ = "traces"
    trace_id = Column(Text, primary_key=True)
    context_json = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default='INIT') # INIT|VALIDATED|GOV_PENDING|APPROVED|EXECUTED|ABORTED|LOCKED
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class Request(Base):
    __tablename__ = "requests"
    request_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, ForeignKey("traces.trace_id"), nullable=False)
    action_type = Column(Text, nullable=False)
    payload_hash = Column(Text, nullable=False)
    nonce = Column(Text, nullable=False)
    device_id = Column(Text, nullable=False)
    aeigis_sig = Column(Text, nullable=False)
    role = Column(Text, nullable=False) # AUTHORITY|OPERATIONS|FINANCE|SYSTEM
    status = Column(String, nullable=False, default='PENDING') # PENDING|VALIDATED|REJECTED|EXECUTABLE|EXECUTED|CONFLICT
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint('trace_id', 'nonce', name='_trace_nonce_uc'),)

class GovernanceRequest(Base):
    __tablename__ = "governance_requests"
    gov_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, ForeignKey("traces.trace_id"), nullable=False)
    action_type = Column(Text, nullable=False)
    payload_hash = Column(Text, nullable=False)
    threshold = Column(Integer, nullable=False)
    required_nodes = Column(JSON, nullable=False) # Array of roles
    status = Column(String, nullable=False, default='PENDING') # PENDING|APPROVED|REJECTED|EXPIRED|LOCKED|EXECUTED
    timeout_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (CheckConstraint('threshold BETWEEN 1 AND 3'),)

class GovernanceApproval(Base):
    __tablename__ = "governance_approvals"
    approval_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    gov_id = Column(String, ForeignKey("governance_requests.gov_id"), nullable=False)
    trace_id = Column(Text, nullable=False)
    approver_id = Column(Text, nullable=False)
    role = Column(Text, nullable=False) # AUTHORITY|OPERATIONS|FINANCE
    decision = Column(Text, nullable=False) # APPROVE|REJECT
    signature_hash = Column(Text, nullable=False)
    device_id = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint('gov_id', 'role', name='_gov_role_uc'),)

class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"
    escrow_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, nullable=False)
    amount_locked = Column(Numeric(18, 2), nullable=False)
    amount_released = Column(Numeric(18, 2), nullable=False, default=0)
    currency = Column(Text, nullable=False)
    fx_rate_locked = Column(Numeric(18, 8))
    status = Column(String, nullable=False, default='LOCKED') # LOCKED|PARTIAL|RELEASED
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class ShadowEvent(Base):
    __tablename__ = "shadow_events"
    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, nullable=False)
    entity = Column(Text, nullable=False)
    event_name = Column(Text, nullable=False)
    payload_hash = Column(Text, nullable=False)
    decision_hash = Column(Text, nullable=False)
    prev_hash = Column(Text)
    this_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class EdgeQueue(Base):
    __tablename__ = "edge_queue"
    seq_no = Column(BigInteger, primary_key=True, autoincrement=True)
    trace_id = Column(Text, nullable=False)
    payload_json = Column(JSONB, nullable=False)
    nonce = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint('trace_id', 'nonce', name='_edge_trace_nonce_uc'),)
