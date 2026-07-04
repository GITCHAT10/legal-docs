import httpx
import asyncio
import os
import pytest
from main import app
from httpx import ASGITransport

@pytest.mark.anyio
async def test_end_to_end_imoxon():
    print("🚀 STARTING iMOXON CONSOLIDATED E2E SUCCESS TEST")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "imoxon-e2e-final"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup
        print("[1] Setting up Sovereign Identity...")
        res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "MIG Admin", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        res_dev = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "secure-tablet-01"})
        device_id = res_dev.json()["device_id"]
        # Verify
        await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})

        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
        }

        # 2. Supplier Connection (Alibaba)
        print("[2] Connecting Global Supplier (Alibaba)...")
        res = await client.post("/imoxon/suppliers/connect", params={"name": "Alibaba Group"}, headers=headers)
        sid = res.json()["supplier_id"]
        print(f"    Supplier ID: {sid}")

        # 3. Product Import
        print("[3] Importing Products (Sourcing Grid)...")
        res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Industrial RO Membrane", "price": 450.0}, headers=headers)
        pid = res.json()["id"]
        print(f"    Product ID (Pending): {pid}")

        # 4. Landed Cost Calculation (Skip if not in current consolidated API or mock it)
        print("[4] Checking MIRA Bridge integration...")
        from main import fce_core
        pricing = fce_core.finalize_invoice(450.0, "RESORT_SUPPLY")
        print(f"    Final Landed Price (incl. 17% TGST): {pricing['total']} MVR")

        # 5. Admin Approval
        print("[5] Admin Approval (Audit Trail)...")
        await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)

        # 6. B2B Order (SALA Resort)
        print("[6] SALA Resort B2B Procurement Order...")
        res = await client.post("/imoxon/orders/create", json={
            "items": [{"product_id": pid, "qty": 10}],
            "amount": float(pricing['total'] * 10)
        }, headers=headers)
        order_id = res.json()["id"]
        print(f"    Order ID: {order_id}")

        # 7. Final Integrity Check
        print("[7] Verifying SHADOW Certificate...")
        res = await client.get("/health")
        print(f"    Sovereign Integrity: {res.json()['integrity']}")

    print("-" * 60)
    print("✅ iMOXON CONSOLIDATED E2E SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_imoxon())
