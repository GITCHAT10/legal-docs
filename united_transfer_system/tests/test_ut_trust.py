import pytest
import asyncio
from sqlalchemy import create_engine
from united_transfer_system.models.base import Base, Journey, Leg, LegType, JourneyStatus, Wallet
from mnos.modules.shadow.models import Evidence
from united_transfer_system.services import (
    booking_service,
    journey_service,
    charter_service,
    finance_service,
    ledger_service
)
from mnos.shared.finance.mira_engine import IdentityTier, TaxProfile
from united_transfer_system.schemas.base import JourneyCreate, LegCreate
import uuid
from datetime import datetime, UTC

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_ut_trust_gates(db):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # --- GATE 1: TAX CORRECTNESS ---
    # Case A: Tourism (Guest)
    guest_fin = finance_service.calculate_ut_financials(1000.0, IdentityTier.GUEST)
    assert guest_fin["tax_type"] == "TGST"
    assert guest_fin["sc"] == 100.0 # 10%
    assert guest_fin["tax"] == 187.0 # 17% of 1100
    assert guest_fin["currency"] == "USD"

    # Case B: Local (Citizen)
    local_fin = finance_service.calculate_ut_financials(1000.0, IdentityTier.CITIZEN)
    assert local_fin["tax_type"] == "GST"
    assert local_fin["sc"] == 0.0
    assert local_fin["tax"] == 80.0 # 8%
    assert local_fin["currency"] == "MVR"

    # --- GATE 2: LEDGER INTEGRITY ---
    trace_id = "TEST-TRACE-001"
    ledger_service.commit_evidence(db, trace_id, "ACTOR_1", "TEST_ACTION", "ENTITY", "E1", {"p": 1})
    ledger_service.commit_evidence(db, trace_id, "ACTOR_1", "TEST_ACTION_2", "ENTITY", "E1", {"p": 2})

    evidences = db.query(Evidence).all()
    assert len(evidences) == 2
    assert evidences[1].previous_hash == evidences[0].current_hash
    assert evidences[1].current_hash != evidences[0].current_hash

    # --- GATE 3: DUAL-QR HARDENING ---
    booking_in = JourneyCreate(
        trace_id=f"TR-{uuid.uuid4().hex[:8]}",
        legs=[LegCreate(type=LegType.SEA, origin="A", destination="B", departure_time=datetime.now(UTC))]
    )
    journey = loop.run_until_complete(booking_service.create_journey(db, obj_in=booking_in, ctx={"aegis_id": "P1", "device_id": "D1"}))
    leg = journey.legs[0]

    # Fail: Wrong Role
    res = journey_service.verify_handshake(db, leg.id, "pickup", leg.master_voucher_code, "D1", "GUEST")
    assert res is False

    # Success: Operator
    res = journey_service.verify_handshake(db, leg.id, "pickup", leg.master_voucher_code, "OP_1", "AUTHORIZED_OPERATOR")
    assert res is True

    # Fail: QR1 Reuse
    res = journey_service.verify_handshake(db, leg.id, "pickup", leg.master_voucher_code, "OP_1", "AUTHORIZED_OPERATOR")
    assert res is False

    # Success: Dropoff
    res = journey_service.verify_handshake(db, leg.id, "dropoff", leg.master_voucher_code, "OP_1", "AUTHORIZED_OPERATOR")
    assert res is True

    # Check Ledger linkage for handshakes
    handshake_ev = db.query(Evidence).filter(Evidence.action == "LEG_DROPOFF").first()
    assert handshake_ev is not None
    assert handshake_ev.trace_id == journey.trace_id

    print("LOCK TRUST LAYER: All Trust Gates Passed.")
    loop.close()
