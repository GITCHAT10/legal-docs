import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard, pms_availability
from datetime import date, timedelta
import uuid

@pytest.mark.anyio
async def test_commercial_idempotency_and_shadow_consistency():
    """
    Scenario: Verify UPOS handles offline synced orders with idempotency and consistent SHADOW events.
    """
    # 1. Setup Identity
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        guest_id = identity_core.create_profile({"full_name": "Idempotent Guest", "profile_type": "guest"})
        device_id = identity_core.bind_device(guest_id, {"fingerprint": "tablet_01"})
        identity_core.verify_identity(guest_id, "SYSTEM")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-AEGIS-IDENTITY": guest_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{guest_id}"
        }

        # Create Order
        order_payload = {"amount": 1500.0, "vendor_id": "VENDOR_A"}
        res = await ac.post("/upos/order/create", json=order_payload, headers=headers)
        assert res.status_code == 200
        intent = res.json()
        intent_id = intent["id"]

        # 2. Replay payment execution (Idempotency Check)
        exec_payload = {"intent_id": intent_id}
        res1 = await ac.post("/upos/payment/execute", json=exec_payload, headers=headers)
        assert res1.status_code == 200
        tx_id1 = res1.json()["transaction_id"]

        # Second attempt should return the same result (Idempotent)
        res2 = await ac.post("/upos/payment/execute", json=exec_payload, headers=headers)
        assert res2.status_code == 200
        tx_id2 = res2.json()["transaction_id"]
        assert tx_id1 == tx_id2

        # 3. Check SHADOW consistency
        # We want events for created, completed, etc.
        from main import shadow_core
        events = [b["event_type"] for b in shadow_core.chain]
        assert "upos.payment.intent.intent" in events
        assert "upos.payment.execute.completed" in events
