import pytest
from sqlalchemy import create_engine
from mnos.modules.boat_ops.models.models import Base, CrewMember, CrewRole, CrewStatus, MaintenanceSchedule
from mnos.modules.boat_ops.services import services
from datetime import datetime, UTC, timedelta, date

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

def test_maintenance_dispatch_block(db):
    # 1. Setup Vessel
    vessel_id = 101

    # 2. Add overdue maintenance
    schedule = MaintenanceSchedule(
        vessel_id=vessel_id,
        maintenance_type="engine_service",
        next_due=datetime.now(UTC) - timedelta(days=1),
        auto_block_dispatch=True
    )
    schedule.ensure_trace_id()
    db.add(schedule)
    db.commit()

    # 3. Check if can dispatch
    allowed, reason = services.maintenance_service.can_dispatch(db, vessel_id)
    assert allowed is False
    assert "Overdue maintenance" in reason
    print(f"Verified: Maintenance Block for vessel {vessel_id} is active.")

def test_crew_license_validation(db):
    # 1. Setup Crew with expired license
    crew = CrewMember(
        full_name="Expired Cap",
        role=CrewRole.CAPTAIN,
        license_number="LIC-EXP",
        license_expiry=date(2023, 1, 1),
        status=CrewStatus.AVAILABLE
    )
    crew.ensure_trace_id()
    db.add(crew)
    db.commit()

    # 2. Attempt shift assignment
    with pytest.raises(ValueError, match="License expired"):
        services.crew_service.assign_shift(
            db, crew_id=crew.id, vessel_id=1,
            start=datetime.now(UTC), end=datetime.now(UTC) + timedelta(hours=4)
        )
    print("Verified: Crew license validation correctly blocks assignment.")
