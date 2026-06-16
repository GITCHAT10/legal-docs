import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
import uuid
import os

from mnos.core.db.session import engine, SessionLocal
from mnos.core.db.base import Base
from mnos.core.fce import service as fce_service
from mnos.modules.inn.reservations import service as inn_service
from mnos.modules.aqua.transfers import service as aqua_service
from mnos.core.fce.mira_export import export_mira_json
from mnos.core.shadow import service as shadow_service
from mnos.modules.inn.reservations.models import ReservationStatus
from mnos.modules.aqua.transfers.models import TransferType

@pytest.fixture(scope="module")
def db():
    os.environ["TESTING"] = "1"
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_single_best_final_stress(db: Session):
    """
    1. Capture a deposit.
    2. Issue a transfer manifest.
    3. Simulate a weather delay + Protection Mode.
    4. Issue a partial refund for the transfer.
    5. Run the Night Audit.
    6. Export to MIRA JSON.
    """
    actor = "stress-tester@mnos.com"

    # Pre-setup: Guest and Reservation
    from mnos.core.aegis.models.guest import Guest
    guest = Guest(first_name="Stress", last_name="Guest", email="stress@mnos.com", trace_id="G-STRESS")
    db.add(guest)
    db.commit()

    res = inn_service.create_reservation(db, reservation_in=type('obj', (object,), {
        "tenant_id": "SALA", "trace_id": "RES-STRESS", "guest_id": guest.id,
        "status": ReservationStatus.CONFIRMED, "total_amount": 0.0, "adults": 2, "children": 0, "stays": []
    }), actor=actor)

    # Manually trigger the event since we are in a unit test without a running background worker
    from mnos.core.events.dispatcher import handle_reservation_created
    handle_reservation_created({"reservation_id": res.id})

    # 1. Capture a deposit
    folio = db.query(fce_service.models.Folio).filter(fce_service.models.Folio.external_reservation_id == str(res.id)).first()
    fce_service.post_transaction(db, folio.id, {"amount": 500.0, "method": "DEPOSIT", "currency": "USD"}, "TX-DEPOSIT", actor=actor)
    assert folio.paid_amount == 500.0

    # 2. Issue a transfer manifest
    transfer_req = aqua_service.create_transfer_request(db, request_in=type('obj', (object,), {
        "tenant_id": "SALA", "trace_id": "TR-STRESS", "guest_id": guest.id, "external_reservation_id": str(res.id),
        "type": TransferType.SEAPLANE, "pickup_location": "MLE", "destination": "SALA", "pickup_time": datetime.now()
    }), actor=actor)

    manifest = aqua_service.models.Manifest(
        tenant_id="SALA", trace_id="MAN-STRESS", transfer_request_id=transfer_req.id, guest_id=guest.id, created_by=actor
    )
    db.add(manifest)
    db.commit()

    # 3. Simulate a weather delay + Protection Mode
    inn_service.trigger_protection_mode(db, res.id, reason="WEATHER_DELAY_SEAPLANE", actor=actor)
    db.refresh(res)
    assert res.protection_mode is True
    assert res.repricing_block_reason == "WEATHER_DELAY_SEAPLANE"

    # 4. Issue a partial refund for the transfer (Simulated by reversing a charge if it was there, or just a payout)
    # Let's post a transfer charge first
    charge = fce_service.post_charge(db, folio.id, {"type": "transfer", "base_amount": 200.0}, "CH-TRANS", actor=actor)
    # Refund 100.0
    fce_service.issue_refund(db, folio.id, {"amount": 100.0, "method": "CASH"}, "REFUND-PARTIAL", actor=actor)
    db.refresh(folio)
    # paid = 500 - 100 = 400
    assert folio.paid_amount == 400.0

    # 5. Run the Night Audit
    inn_service.run_night_audit(db, date.today(), actor=actor)

    # 6. Export to MIRA JSON
    invoice = fce_service.finalize_invoice(db, folio.id, actor=actor)
    mira_export = export_mira_json(invoice)

    assert "verification_hash" in mira_export
    assert mira_export["standard"] == "MIRA-EOS-2026"

    # Verify SHADOW Integrity
    from mnos.core.shadow.models import Evidence
    evidences = db.query(Evidence).order_by(Evidence.id).all()
    # Check chain
    prev_hash = "GENESIS"
    for ev in evidences:
        assert ev.previous_hash == prev_hash
        prev_hash = ev.current_hash

    print("\n[STRESS TEST PASSED] SHADOW Chain Verified.")
