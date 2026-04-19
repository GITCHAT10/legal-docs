import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CustomsClearanceRequest(Base):
    __tablename__ = "customs_clearance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(64), unique=True, nullable=False)
    container_id = Column(String(32), nullable=False)
    declaration_type = Column(String(20), nullable=False)
    commodity = Column(String(64), nullable=False)
    origin_site_id = Column(String(64))
    declared_weight = Column(Numeric(14, 3), nullable=False)
    destination_country = Column(String(4))
    requested_by_officer_id = Column(String(64))
    status = Column(String(20), nullable=False)
    risk_score = Column(Numeric(5, 4))
    clearance_token = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CustomsClearanceBatch(Base):
    __tablename__ = "customs_clearance_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clearance_request_id = Column(UUID(as_uuid=True), ForeignKey("customs_clearance_requests.id", ondelete="CASCADE"))
    batch_id = Column(String(64), nullable=False)
    provenance_status = Column(String(20))
    yield_status = Column(String(20))
    settlement_status = Column(String(20))

class CustomsReview(Base):
    __tablename__ = "customs_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clearance_request_id = Column(UUID(as_uuid=True), ForeignKey("customs_clearance_requests.id"))
    review_status = Column(String(20), nullable=False)
    reviewer_id = Column(String(64))
    decision_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
