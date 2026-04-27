import pytest
import asyncio
from sqlalchemy import create_engine
from united_transfer_system.models.base import Base, Asset, LegType
from united_transfer_system.services import booking_service, journey_service
from united_transfer_system.schemas.base import JourneyCreate, LegCreate
import uuid
from datetime import datetime, UTC

# Universal API Stress Test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    from sqlalchemy.orm import sessionmaker
    from mnos.core.db.session import SovereignSession
    SessionLocal = sessionmaker(class_=SovereignSession, autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_high_concurrency_gps(db):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 1. Create a baseline leg
    booking_in = JourneyCreate(
        trace_id=str(uuid.uuid4()),
        legs=[LegCreate(type=LegType.SEA, origin="MLE", destination="KAF", departure_time=datetime.now(UTC))]
    )
    journey = loop.run_until_complete(booking_service.create_journey(db, obj_in=booking_in, ctx={"aegis_id": "P1", "trace_id": "STRESS-T1"}))
    leg_id = journey.legs[0].id

    # 2. Simulate 50 concurrent GPS updates
    async def send_gps(i):
        journey_service.process_telemetry(db, leg_id=leg_id, lat=4.0 + (i*0.001), lon=73.0 + (i*0.001))

    tasks = [send_gps(i) for i in range(50)]
    loop.run_until_complete(asyncio.gather(*tasks))

    # 3. Verify final state
    from united_transfer_system.models.base import Telemetry
    count = db.query(Telemetry).filter(Telemetry.leg_id == leg_id).count()
    assert count == 50
    print(f"Stress Test: Processed {count} concurrent GPS updates successfully.")
    loop.close()

def test_partner_onboarding_scale(db):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    from united_transfer_system.schemas.base import PartnerCreate
    from united_transfer_system.models.base import PartnerTier

    async def create_p(i):
        p_in = PartnerCreate(name=f"Partner-{i}", tier=PartnerTier.HARDENED)
        await booking_service.create_partner(db, obj_in=p_in)

    tasks = [create_p(i) for i in range(20)]
    loop.run_until_complete(asyncio.gather(*tasks))

    from united_transfer_system.models.base import Partner
    count = db.query(Partner).count()
    assert count == 20
    print(f"Stress Test: Registered {count} partners concurrently.")
    loop.close()
