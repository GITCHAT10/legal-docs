import pytest
from sqlalchemy.orm import Session
from mnos.core.db.session import SessionLocal
from mnos.modules.fce import tax_logic, escrow
import uuid

def test_tax_calculation_accuracy():
    # Base 1000 + 10% SC (100) = 1100. 17% TGST on 1100 = 187. Total = 1287
    res = tax_logic.calculate_maldives_taxes(1000.0, None)
    assert res["service_charge"] == 100.0
    assert res["tgst"] == 187.0
    assert res["total_amount"] == 1287.0

def test_escrow_lock_release():
    db = SessionLocal()
    trace_id = f"TR-{uuid.uuid4().hex}"
    assert escrow.lock_funds(db, trace_id, 1000.0) == True
    assert escrow.release_funds(db, trace_id, True) == True
    db.close()
