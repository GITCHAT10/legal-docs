import pytest
import asyncio
from sqlalchemy import create_engine
from united_transfer_system.models.base import Base, Journey, Leg, LegType, JourneyStatus, Wallet
from united_transfer_system.services import booking_service, journey_service, charter_service, finance_service
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

def test_ut_full_lifecycle(db):
    # 1. Multi-leg Booking
    trace_id = f"TR-{uuid.uuid4().hex[:8]}"
    booking_in = JourneyCreate(
        trace_id=trace_id,
        legs=[
            LegCreate(type=LegType.LAND, origin="Airport", destination="Terminal 1", departure_time=datetime.now(UTC)),
            LegCreate(type=LegType.SEA, origin="Terminal 1", destination="Kafau Resort", departure_time=datetime.now(UTC))
        ]
    )
    ctx = {"aegis_id": "PARTNER_001", "device_id": "DEV_UT_01"}

    # Run async function in sync test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    journey = loop.run_until_complete(booking_service.create_journey(db, obj_in=booking_in, ctx=ctx))

    assert journey.trace_id == trace_id
    assert len(journey.legs) == 2

    # 2. Charter Consolidation
    # Add more legs to trigger threshold (5)
    for i in range(4):
        booking_in_loop = JourneyCreate(
            trace_id=f"TR-{uuid.uuid4().hex[:8]}",
            legs=[LegCreate(type=LegType.SEA, origin="Terminal 1", destination="Other Resort", departure_time=datetime.now(UTC))]
        )
        loop.run_until_complete(booking_service.create_journey(db, obj_in=booking_in_loop, ctx=ctx))

    manifest = charter_service.consolidate_bookings(db)
    assert manifest is not None
    assert manifest.status == "draft"

    # 3. GPS Telemetry
    leg_id = journey.legs[0].id
    telemetry = journey_service.process_telemetry(db, leg_id=leg_id, lat=4.175, lon=73.509, speed=25.0)
    assert telemetry.leg_id == leg_id

    # 4. Dual-QR Handshake & Instant Payout
    # Assign provider
    leg = db.query(Leg).filter(Leg.id == leg_id).first()
    leg.provider_id = "VESSEL_007"
    db.commit()

    # Scan 1: Pickup
    journey_service.verify_handshake(db, leg_id=leg_id, scan_type="pickup", master_code=leg.master_voucher_code)
    assert leg.qr1_verified is True

    # Scan 2: Dropoff -> Trigger Payout
    journey_service.verify_handshake(db, leg_id=leg_id, scan_type="dropoff", master_code=leg.master_voucher_code)
    assert leg.qr2_verified is True

    # Check Wallet
    wallet = db.query(Wallet).filter(Wallet.owner_id == "VESSEL_007").first()
    assert wallet.balance > 0
    assert len(wallet.transactions) == 1

    # 5. Finance Tax Split
    split = finance_service.calculate_ut_split(100.0)
    assert split["tgst"] == 18.7 # 100 * 1.1 * 0.17 = 18.7
    assert split["ggst"] == 8.0 # 100 * 0.08 = 8.0

    print("UT Genesis Lifecycle Test Passed!")
    loop.close()
