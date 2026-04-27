import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from united_transfer_system.models.base import Base, Asset, Partner, LegType
from united_transfer_system.services import booking_service, journey_service
from united_transfer_system.schemas.base import JourneyCreate, LegCreate, HandshakeInput
import uuid
from datetime import datetime, UTC, timedelta

# ORCA Control Tower Simulator: MLE Hub Operations
# Models 1 day of real Maldives transfers

SQLALCHEMY_DATABASE_URL = "sqlite:///./orca_sim.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_sim_assets(db):
    # Fleet setup
    assets = [
        Asset(name="Speedboat-01", type="vessel", capacity=12),
        Asset(name="Speedboat-02", type="vessel", capacity=12),
        Asset(name="Van-Airport-01", type="vehicle", capacity=7),
    ]
    for a in assets:
        a.ensure_trace_id()
        db.add(a)
    db.commit()

async def run_orca_cycle():
    db = SessionLocal()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    setup_sim_assets(db)

    print("ORCA SIM: Initiating MLE Hub Morning Cycle...")

    # 1. Multi-leg Journey Request (MLE -> Jetty -> Resort)
    trace_id = f"ORCA-{uuid.uuid4().hex[:6]}"
    booking_in = JourneyCreate(
        trace_id=trace_id,
        legs=[
            LegCreate(type=LegType.LAND, origin="Arrivals", destination="Jetty No 5", departure_time=datetime.now(UTC)),
            LegCreate(type=LegType.SEA, origin="Jetty No 5", destination="Kafau Resort", departure_time=datetime.now(UTC) + timedelta(minutes=15))
        ]
    )

    ctx = {"aegis_id": "RESORT_ADMIN", "device_id": "ORCA-CONSOLE-01"}
    journey = await booking_service.create_journey(db, obj_in=booking_in, ctx=ctx)
    print(f"ORCA SIM: Journey {journey.trace_id} Created with {len(journey.legs)} legs.")

    # 2. Assign Asset to Leg 1 (Land)
    leg1 = journey.legs[0]
    leg1.asset_id = 3 # Van
    leg1.provider_id = "DRIVER-ALI"
    db.commit()

    # 3. Execution: Boarding Land Leg
    print("ORCA SIM: Boarding Van at Arrivals...")
    journey_service.verify_handshake(
        db,
        leg_id=leg1.id,
        scan_type="pickup",
        master_code=leg1.master_voucher_code,
        actor_id="DRIVER-ALI",
        actor_role="AUTHORIZED_OPERATOR"
    )

    # 4. GPS Stream (Land)
    print("ORCA SIM: Van in transit to Jetty...")
    journey_service.process_telemetry(db, leg_id=leg1.id, lat=4.191, lon=73.525)

    # 5. Completion: Arrive at Jetty
    journey_service.verify_handshake(
        db,
        leg_id=leg1.id,
        scan_type="dropoff",
        master_code=leg1.master_voucher_code,
        actor_id="DRIVER-ALI",
        actor_role="AUTHORIZED_OPERATOR"
    )
    await journey_service.confirm_arrival(db, leg_id=leg1.id)
    print("ORCA SIM: Land Leg Completed. Payment Released.")

    db.close()
    print("ORCA SIM: Cycle Finished Successfully.")

if __name__ == "__main__":
    asyncio.run(run_orca_cycle())
