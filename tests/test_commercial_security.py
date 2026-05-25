import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard
from datetime import date, timedelta
import uuid

@pytest.mark.anyio
async def test_upos_guard_bypass_prevention():
    """
    Scenario: Verify UPOS cannot move money without ExecutionGuard.
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        guest_id = identity_core.create_profile({"full_name": "Shield Guest", "profile_type": "guest"})
        device_id = identity_core.bind_device(guest_id, {"fingerprint": "secure_hw"})
        identity_core.verify_identity(guest_id, "SYSTEM")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Attempt call without headers
        order_payload = {"amount": 100.0, "vendor_id": "VENDOR_A"}
        res = await ac.post("/upos/order/create", json=order_payload)
        # ExecutionGuardMiddleware blocks it first and returns 403 (for strict paths) or 401 (for dual paths)
        # Since /upos is strict, it returns 403
        assert res.status_code == 403

        # 2. Attempt call with session but for strict path
        headers_session = {"X-AEGIS-SESSION": "some_session"}
        res = await ac.post("/upos/order/create", json=order_payload, headers=headers_session)
        assert res.status_code == 403 # Strict path requires Identity + Device

        # 3. Valid headers
        headers_valid = {
            "X-AEGIS-IDENTITY": guest_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{guest_id}"
        }
        res = await ac.post("/upos/order/create", json=order_payload, headers=headers_valid)
        assert res.status_code == 200
