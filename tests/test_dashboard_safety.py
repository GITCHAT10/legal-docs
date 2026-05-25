import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard, shadow_core
import uuid

@pytest.mark.anyio
async def test_orca_dashboard_payload_safety():
    """
    Scenario: Verify ORCA dashboard handles both online and offline payloads safely.
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        staff_id = identity_core.create_profile({"full_name": "Dashboard Ops", "profile_type": "staff"})
        device_id = identity_core.bind_device(staff_id, {"fingerprint": "dashboard_hw"})
        identity_core.verify_identity(staff_id, "SYSTEM")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-AEGIS-IDENTITY": staff_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{staff_id}"
        }

        # 1. Simulate an offline sync entry with a malformed pricing payload in SHADOW
        with guard.sovereign_context(SYSTEM_CTX):
            shadow_core.commit("offline_sync.pos", "SYSTEM", {
                "trace_id": "OFFLINE-001",
                "pricing": None # Potential crash point if not handled (get() vs key access)
            })
            shadow_core.commit("offline_sync.booking", "SYSTEM", {
                "trace_id": "OFFLINE-002",
                # missing "pricing" key entirely
            })

        # 2. Fetch dashboard summary
        res = await ac.get("/orca/dashboard/summary", headers=headers)
        assert res.status_code == 200
        summary = res.json()
        assert summary["status"] == "OPERATIONAL"
        # Total revenue should be 0 because pricing was malformed, but it shouldn't CRASH
        assert summary["metrics"]["total_revenue_mvr"] >= 0
