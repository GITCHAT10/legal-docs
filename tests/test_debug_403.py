import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard

@pytest.mark.anyio
async def test_debug_403():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        sid = identity_core.create_profile({"full_name": "S1", "profile_type": "supplier"})
        did = identity_core.bind_device(sid, {"fingerprint": "d1"})
        identity_core.profiles[sid]["verification_status"] = "verified"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-AEGIS-IDENTITY": sid,
            "X-AEGIS-DEVICE": did,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{sid}"
        }
        res = await ac.post("/prestige/supplier-portal/contracts/upload", params={"supplier_id":"S1", "resort_name":"R1", "file_name":"f1"}, headers=headers)
        print(f"STATUS: {res.status_code}")
        print(f"BODY: {res.text}")
