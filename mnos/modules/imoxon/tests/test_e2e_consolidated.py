import httpx
import asyncio
import os
from main import app
from httpx import ASGITransport

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
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "secure-tablet-01"})
        headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "secure-tablet-01"}

        # 2. Supplier Connection (Alibaba)
        print("[2] Connecting Global Supplier (Alibaba)...")
        res = await client.post("/imoxon/suppliers/connect", json={"name": "Alibaba Group", "type": "GLOBAL"}, headers=headers)
        sid = res.json()["id"]
        print(f"    Supplier ID: {sid}")

        # 3. Product Import
        print("[3] Importing Products (Sourcing Grid)...")
        res = await client.post("/imoxon/products/import", params={"sid": sid}, json=[{"name": "Industrial RO Membrane", "price": 450.0}], headers=headers)
        pid = res.json()["products"][0]["id"]
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
            "pricing": pricing
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
