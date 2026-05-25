import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard, shadow_core, prestige_portal, iluvia_orchestrator
from mnos.modules.prestige.supplier_portal.models import ChannelType, VisibilityScope, RateApprovalStatus
from mnos.modules.pms.adapters.placeholders import OperaAdapter
from mnos.shared.exceptions import ExecutionValidationError
import uuid

@pytest.mark.anyio
async def test_area1_pms_abstraction():
    # 1. Reject incomplete payload
    from mnos.modules.pms.adapters.base_adapter import CanonicalBooking
    with pytest.raises(Exception):
        CanonicalBooking(source_system="OPERA", arrival_date="2024-01-01")

    # 2. External ID vs Truth ID
    adapter = OperaAdapter()
    raw = {"res_id": "EXT-123", "hotel_code": "H1", "arrival": "2024-10-10", "departure": "2024-10-15", "room_type": "V", "rate_amount": 100, "currency": "USD"}
    canonical = adapter.normalize(raw)
    assert canonical.external_reservation_id == "EXT-123"

@pytest.mark.anyio
async def test_area2_rate_sheet_logic():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        supp_id = identity_core.create_profile({"full_name": "S1", "profile_type": "supplier"})
        supp_dev = identity_core.bind_device(supp_id, {"fingerprint": "d1"})
        identity_core.profiles[supp_id]["verification_status"] = "verified"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"x-aegis-identity": supp_id, "x-aegis-device": supp_dev, "x-aegis-signature": f"VALID_SIG_FOR_{supp_id}"}

        payload = {"supplier_id": supp_id, "product_id": "P1", "channel_type": ChannelType.B2C_DIRECT, "visibility_scope": VisibilityScope.PUBLIC, "base_net_rate": 1000.0}
        res = await ac.post("/prestige/supplier-portal/rate-sheets/upload", json=payload, headers=headers)
        rate_id = res.json()["rate_id"]

        # Try to jump to CMO without correct role
        res = await ac.post(f"/prestige/supplier-portal/cmo/market-strategy?rate_id={rate_id}", headers=headers)
        assert res.status_code == 403

@pytest.mark.anyio
async def test_area5_bubble_orchestrator():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with pytest.raises(ExecutionValidationError) as exc:
        with guard.sovereign_context(SYSTEM_CTX):
            iluvia_orchestrator.confirm_real_world("NON-EXISTENT", {"type": "QR_SCAN", "valid": True})
    assert "ORDER_NOT_FOUND" in str(exc.value)

@pytest.mark.anyio
async def test_area4_spoof_prevention():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt to spoof SYSTEM identity on a guarded route
        headers = {
            "x-aegis-identity": "SYSTEM",
            "x-aegis-device": "any",
            "x-aegis-signature": "any"
        }
        res = await ac.post("/imoxon/orders/create", json={}, headers=headers)
        assert res.status_code in [401, 403]
