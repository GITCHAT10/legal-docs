import pytest
from sqlalchemy.orm import Session
from mnos.core.db.session import SessionLocal
from mnos.modules.fce import service as fce_service, models as fce_models
from mnos.modules.maintain import service as maintain_service, enums as maintain_enums
from mnos.interfaces.prestige.guests import models as guest_models
from mnos.core.db.sync_buffer import sync_buffer
import uuid

def test_finalize_invoice():
    db = SessionLocal()
    # Mock open folio
    folio = fce_service.open_folio(db, str(uuid.uuid4()), f"TR-{uuid.uuid4().hex[:6]}")
    invoice = fce_service.finalize_invoice(db, folio_id=folio.id)
    assert invoice.total_amount == folio.total_amount
    db.refresh(folio)
    assert folio.status == fce_models.FolioStatus.FINALIZED
    db.close()

def test_maintenance_trace_id():
    db = SessionLocal()
    trace_id = f"TR-MAINT-{uuid.uuid4().hex[:6]}"
    ticket = maintain_service.create_ticket(db, room_id=1, title="Test", description="Test",
                                          priority=maintain_enums.TicketPriority.P3, trace_id=trace_id)
    assert ticket.trace_id == trace_id
    db.close()

def test_sync_buffer_commit_before_clear():
    db = SessionLocal()
    sync_buffer.queue_transaction("SYNC-TR-1", {"data": "test"})
    res = sync_buffer.process_sync(db)
    assert "SYNC-TR-1" in res
    db.close()
