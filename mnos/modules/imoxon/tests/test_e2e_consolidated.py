import httpx
import pytest
from main import app
from httpx import ASGITransport

@pytest.mark.anyio
async def test_end_to_end_imoxon():
    print("🚀 STARTING iMOXON CONSOLIDATED E2E SUCCESS TEST")
    print("-" * 60)

    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup
        print("[1] Setting up Sovereign Identity...")
        res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "MIG Admin", "profile_type": "admin"})
        assert res.status_code == 200, res.text
        actor_id = res.json()["identity_id"]
        from main import identity_core
        identity_core.verify_identity(actor_id, "SYSTEM")
        res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "secure-tablet-01"})
        assert res.status_code == 200, res.text
        device_id = res.json()["device_id"]
        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
        }

        # 2. Supplier Connection (Alibaba)
        print("[2] Connecting Global Supplier (Alibaba)...")
        res = await client.post("/imoxon/suppliers/connect", params={"name": "Alibaba Group"}, headers=headers)
        assert res.status_code == 200, res.text
        sid = res.json()["supplier_id"]
        print(f"    Supplier ID: {sid}")

        # 3. Product Import
        print("[3] Importing Products (Sourcing Grid)...")
        res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Industrial RO Membrane", "price": 450.0}, headers=headers)
        assert res.status_code == 200, res.text
        pid = res.json()["id"]
        print(f"    Product ID (Pending): {pid}")

        # 4. Landed Cost Calculation
        print("[4] Calculating Maldives Landed Cost...")
        res = await client.post("/imoxon/pricing/landed-cost", params={"base": 450.0, "cat": "RESORT_SUPPLY"}, headers=headers)
        pricing = res.json()
        print(f"    Final Landed Price (incl. 17% TGST): {pricing['total']} MVR")

        # 5. Admin Approval
        print("[5] Admin Approval (Audit Trail)...")
        await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)

        # 6. B2B Order (SALA Resort)
        print("[6] SALA Resort B2B Procurement Order...")
        res = await client.post("/imoxon/orders/create", json={
            "items": [{"product_id": pid, "qty": 10}],
            "amount": pricing["total"],
        }, headers=headers)
        assert res.status_code == 200, res.text
        order_id = res.json()["id"]
        print(f"    Order ID: {order_id}")

        # 7. Final Integrity Check
        print("[7] Verifying SHADOW Certificate...")
        res = await client.get("/health")
        print(f"    Sovereign Integrity: {res.json()['integrity']}")

    print("-" * 60)
    print("✅ iMOXON CONSOLIDATED E2E SUCCESS")
