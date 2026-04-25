import pytest
from sqlalchemy.orm import Session
from mnos.interfaces.prestige.guests import models as guest_models
from mnos.modules.inn.reservations import service as res_service, schemas as res_schemas, models as res_models
from mnos.modules.fce import service as fce_service, models as fce_models
from mnos.core.db.session import SessionLocal
import uuid
from datetime import date

def test_full_booking_flow():
    from mnos.core.db.base_class import Base
    from mnos.core.db.session import engine
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Setup Room
        room_number = f"101-{uuid.uuid4().hex[:4]}"
        room = res_service.create_room(db, room_in=res_schemas.RoomCreate(
            tenant_id="test", trace_id=str(uuid.uuid4()), room_number=room_number,
            room_type="DELUXE", status=res_models.RoomStatus.READY, base_price=500.0, capacity=2
        ))

        # 2. Create Reservation (Triggers Transfer event)
        trace_id = f"TEST-RES-{uuid.uuid4().hex[:8]}"
        res = res_service.create_reservation(db, reservation_in=res_schemas.ReservationCreate(
            tenant_id="test", trace_id=trace_id, guest_id=1, status=res_models.ReservationStatus.CONFIRMED,
            total_amount=500.0, adults=2, children=0,
            stays=[res_schemas.StayCreate(room_id=room.id, check_in_date=date.today(), check_out_date=date.today())]
        ))
        assert res.status == res_models.ReservationStatus.CONFIRMED

        # 3. Open Folio and Post Charge
        folio = fce_service.open_folio(db, reservation_id=str(res.id), trace_id=f"FOL-{trace_id}")
        fce_service.post_charge(db, folio_id=folio.id, charge_data={
            "type": "ROOM", "base_amount": 500.0, "description": "Room Charge"
        }, trace_id=f"CHG-{trace_id}")

        db.refresh(folio)
        assert folio.total_amount > 500.0 # Includes taxes

        # 4. Finalize Invoice
        invoice = fce_service.finalize_invoice(db, folio_id=folio.id, actor="TEST_USER")
        assert invoice.total_amount == folio.total_amount

        db.refresh(folio)
        assert folio.status == fce_models.FolioStatus.FINALIZED

    finally:
        db.close()

if __name__ == "__main__":
    test_full_booking_flow()
