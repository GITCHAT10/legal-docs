from mnos.shared.guard.test_signer import aegis_sign
import pytest
from decimal import Decimal
from mnos.api import verify_session, calculate_folio, execute_sovereign
from mnos.core.security.aegis import aegis

def test_api_verify_session():
    import time
    ctx = {
        "user_id": "API-TEST",
        "session_id": "S-API-01",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-API-01"
    }
    ctx["signature"] = aegis_sign(ctx)
    assert verify_session(ctx) is True

def test_api_calculate_folio():
    res = calculate_folio(Decimal("100.00"), stay_hours=10.0)
    assert res["green_tax"] == Decimal("0.00")
    assert res["mira_compliant"] is True

def test_api_execute_sovereign():
    import time
    ctx = {
        "user_id": "API-EXEC",
        "session_id": "S-API-02",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-API-02"
    }
    ctx["signature"] = aegis_sign(ctx)

    def mock_logic(p): return "api_ok"

    res = execute_sovereign(
        action_type="nexus.booking.created",
        payload={"data": "test"},
        session_context=ctx,
        logic=mock_logic
    )
    assert res == "api_ok"
