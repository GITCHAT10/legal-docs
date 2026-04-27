import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from united_transfer_system.models.base import Base as UTBase, Asset, LegType
from mnos.modules.boat_ops.models.models import Base as BoatBase, CrewMember, CrewRole, CrewStatus
from mnos.modules.flight_mvp.models.models import Base as FlightBase
from mnos.modules.boat_ops.services import services as boat_services
from mnos.modules.flight_mvp.services.engine import flight_mvp_engine
from united_transfer_system.services import booking_service, journey_service
from united_transfer_system.schemas.base import JourneyCreate, LegCreate
import uuid
from datetime import datetime, UTC, timedelta, date

# Enhanced ORCA Simulator: Full Cycle
# Models Flight -> Boat Ops -> Payout

SQLALCHEMY_DATABASE_URL = "sqlite:///./orca_enhanced.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_sim_data(db):
    # Fleet setup
    asset = Asset(name="Speedboat-ORCA", type="vessel", capacity=12)
    asset.ensure_trace_id()
    db.add(asset)

    # Crew setup
    crew = CrewMember(
        full_name="Captain Ahmed",
        role=CrewRole.CAPTAIN,
        license_number="LIC-960-001",
        license_expiry=date(2027, 1, 1),
        phone_mv="+9607771234",
        status=CrewStatus.AVAILABLE
    )
    crew.ensure_trace_id()
    db.add(crew)
    db.commit()
    return asset, crew

async def run_enhanced_orca():
    # Merge all metadata for simulation DB
    UTBase.metadata.drop_all(bind=engine)
    BoatBase.metadata.drop_all(bind=engine)
    FlightBase.metadata.drop_all(bind=engine)

    UTBase.metadata.create_all(bind=engine)
    BoatBase.metadata.create_all(bind=engine)
    FlightBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    asset, crew = setup_sim_data(db)

    print("ORCA ENHANCED: Starting Morning Operations...")

    # 1. Flight Arrival (MVP)
    print("ORCA ENHANCED: Tracking Flight EK652...")
    flt_session = await flight_mvp_engine.create_mvp_session(
        db,
        booking_id="B-RES-001",
        flight_number="EK652",
        origin_iata="DXB",
        scheduled_arrival=datetime.now(UTC) + timedelta(hours=1),
        guest_count=4
    )

    # 2. Crew Assignment (Boat Ops)
    print(f"ORCA ENHANCED: Assigning {crew.full_name} to {asset.name}...")
    shift = boat_services.crew_service.assign_shift(
        db, crew_id=crew.id, vessel_id=asset.id,
        start=datetime.now(UTC), end=datetime.now(UTC) + timedelta(hours=8)
    )

    # 3. Flight Delay Detection & UT Auto-Adjust
    print("ORCA ENHANCED: EK652 Delayed 45min detected.")
    await flight_mvp_engine.check_for_delays(db, flt_session.id)

    # 4. Fuel Logging (Crew App)
    print("ORCA ENHANCED: Captain Ahmed logging fuel...")
    boat_services.fuel_service.log_fuel(db, vessel_id=asset.id, liters=450.0, atoll="North Male", logged_by=crew.id)

    # 5. Trip Execution
    booking_in = JourneyCreate(
        trace_id=f"ORCA-{uuid.uuid4().hex[:6]}",
        legs=[LegCreate(type=LegType.SEA, origin="MLE Airport", destination="Resort", departure_time=datetime.now(UTC))]
    )
    journey = await booking_service.create_journey(db, obj_in=booking_in, ctx={"aegis_id": "OP", "trace_id": "T1"})
    leg = journey.legs[0]
    leg.asset_id = asset.id
    leg.provider_id = f"CREW-{crew.id}"
    db.commit()

    print("ORCA ENHANCED: Boarding complete. Starting trip.")
    journey_service.verify_handshake(db, leg.id, "pickup", leg.master_voucher_code, str(crew.id), "AUTHORIZED_OPERATOR")

    print("ORCA ENHANCED: Trip completed. Triggering payout.")
    journey_service.verify_handshake(db, leg.id, "dropoff", leg.master_voucher_code, str(crew.id), "AUTHORIZED_OPERATOR")
    await journey_service.confirm_arrival(db, leg_id=leg.id)

    print("ORCA ENHANCED: All operations verified. System Closed.")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_enhanced_orca())
