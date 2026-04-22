import pytest
from decimal import Decimal
from mnos.api import verify_session, calculate_folio, execute_sovereign
from mnos.core.security.aegis import aegis

def test_api_verify_session():
    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis.sign_session(ctx)
    assert verify_session(ctx) is True

def test_api_calculate_folio():
    res = calculate_folio(Decimal("100.00"), stay_hours=10.0)
    assert res["green_tax"] == Decimal("0.00")
    assert res["mira_compliant"] is True

def test_api_execute_sovereign():
    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis.sign_session(ctx)

    def mock_logic(p): return "api_ok"

    res = execute_sovereign(
        action_type="nexus.booking.created",
        payload={"data": "test"},
        session_context=ctx,
        logic=mock_logic
    )
    assert res == "api_ok"
