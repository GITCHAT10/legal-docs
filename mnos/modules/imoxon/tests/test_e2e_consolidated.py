import httpx
import pytest
import os
from main import app
from httpx import ASGITransport

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_end_to_end_imoxon():
    print("🚀 STARTING iMOXON CONSOLIDATED E2E SUCCESS TEST")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "imoxon-e2e-final"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup
        print("[1] Setting up Sovereign Identity...")
        res = await client.post("/aegis/identity/create", json={"full_name": "MIG Admin", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        res = await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "secure-tablet-01"})
        device_id = res.json()["device_id"]

        # Verify the identity so it can perform critical actions
        await client.post("/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYS"})

        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
        }

        # 2. Supplier Connection (Alibaba)
        print("[2] Connecting Global Supplier (Alibaba)...")
        res = await client.post("/imoxon/suppliers/connect", json={"name": "Alibaba Group", "type": "GLOBAL"}, headers=headers)
        assert res.status_code == 200
        sid = res.json()["id"]
        print(f"    Supplier ID: {sid}")

        # 3. Product Import
        print("[3] Importing Products (Sourcing Grid)...")
        res = await client.post("/imoxon/products/import", params={"sid": sid}, json=[{"name": "Industrial RO Membrane", "price": 450.0}], headers=headers)
        assert res.status_code == 200
        pid = res.json()["products"][0]["id"]
        print(f"    Product ID (Pending): {pid}")

        # 4. Landed Cost Calculation
        print("[4] Calculating Maldives Landed Cost...")
        res = await client.post("/imoxon/pricing/landed-cost", params={"base": 450.0, "cat": "RESORT_SUPPLY"}, headers=headers)
        assert res.status_code == 200
        pricing = res.json()
        print(f"    Final Landed Price (incl. 17% TGST): {pricing['total']} MVR")

        # 5. Admin Approval
        print("[5] Admin Approval (Audit Trail)...")
        res = await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)
        assert res.status_code == 200

        # 6. B2B Order (SALA Resort)
        print("[6] SALA Resort B2B Procurement Order...")
        res = await client.post("/imoxon/orders/create", json={
            "items": [{"product_id": pid, "qty": 10}],
            "pricing": pricing
        }, headers=headers)
        assert res.status_code == 200
        order_id = res.json()["id"]
        print(f"    Order ID: {order_id}")

        # 7. Final Integrity Check
        print("[7] Verifying SHADOW Certificate...")
        res = await client.get("/health")
        assert res.status_code == 200
        print(f"    Sovereign Integrity: {res.json()['integrity']}")

    print("-" * 60)
    print("✅ iMOXON CONSOLIDATED E2E SUCCESS")
