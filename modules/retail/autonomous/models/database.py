from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timezone
import uuid

Base = declarative_base()

# Database setup
DATABASE_URL = "sqlite:///./mars_retail.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RetailStore(Base):
    __tablename__ = 'retail_stores'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    property_id = Column(String) # Mapping to INN property
    name = Column(String, nullable=False)
    mode = Column(String, default="ASSISTED_AUTONOMOUS") # ASSISTED_AUTONOMOUS, FULL_AUTONOMOUS
    hardware_profile_json = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RetailHardwareNode(Base):
    __tablename__ = 'retail_hardware_nodes'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey('retail_stores.id'))
    node_type = Column(String) # CAMERA, SHELF, GATE, EDGE_BOX, RFID
    node_identifier = Column(String, unique=True)
    zone = Column(String)
    status = Column(String)
    trust_score = Column(Numeric(precision=5, scale=4), default=1.0)
    config_json = Column(JSON)
    last_seen_at = Column(DateTime)
    last_heartbeat_at = Column(DateTime)

class RetailSession(Base):
    __tablename__ = 'retail_sessions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    aegis_user_id = Column(UUID(as_uuid=True), nullable=False)
    store_id = Column(String, nullable=False)
    status = Column(String, default="OPEN") # OPEN, ACTIVE, EXITED, SETTLED, FLAGGED, CANCELLED
    auth_type = Column(String) # NFC, QR, FACE
    confidence_score = Column(Numeric(precision=5, scale=4))
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime)
    trace_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    idempotency_key = Column(String, unique=True)
    settlement_id = Column(UUID(as_uuid=True))
    receipt_id = Column(String)
    anomaly_flags = Column(JSON) # List of anomaly flags
    evidence_bundle = Column(JSON) # SHADOW canonical evidence
    reviewer_id = Column(UUID(as_uuid=True))
    review_reason = Column(String)
    parent_session_id = Column(UUID(as_uuid=True)) # For reversals
    shadow_hash = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class RetailSessionEvent(Base):
    __tablename__ = 'retail_session_events'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('retail_sessions.id'))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String) # ENTRY, PICK, PUT, MOVE, EXIT, REVIEW, SETTLE
    source = Column(String) # VISION, SHELF, RFID, GATE
    hardware_id = Column(String)
    product_id = Column(String, nullable=True)
    qty = Column(Numeric(precision=10, scale=2), nullable=True)
    confidence = Column(Numeric(precision=5, scale=4))
    trust_score_at_event = Column(Numeric(precision=5, scale=4))
    is_duplicate = Column(Boolean, default=False)
    payload_json = Column(JSON)
    trace_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RetailSessionCartItem(Base):
    __tablename__ = 'retail_session_cart_items'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('retail_sessions.id'))
    product_id = Column(String, nullable=False)
    qty = Column(Numeric(precision=10, scale=2), nullable=False)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    subtotal = Column(Numeric(precision=10, scale=2), nullable=False)
    price_snapshot = Column(JSON) # { "base_price": ..., "currency": ..., "timestamp": ... }
    confidence_score = Column(Numeric(precision=5, scale=4))
    anomaly_flags = Column(JSON)
    status = Column(String, default="ACTIVE") # ACTIVE, REMOVED, CONFIRMED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
