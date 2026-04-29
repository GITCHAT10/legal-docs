import httpx
import asyncio
import os
import json
from main import app
from httpx import ASGITransport

async def simulate_bridge():
    print("🚀 STARTING REAL-WORLD BRIDGE SIMULATION (RC1-PRODUCTION)")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "bridge-sim-2026"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Identities
        res = await client.post("/aegis/identity/create", json={"full_name": "Resort Manager", "profile_type": "admin"})
        manager_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": manager_id}, json={"fingerprint": "mgr-dev"})

        # Identity with verified National ID for settlement
        res = await client.post("/aegis/identity/create", json={"full_name": "Finance Officer", "profile_type": "staff"})
        finance_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": finance_id}, json={"fingerprint": "fin-dev"})

        h_mgr = {"X-AEGIS-IDENTITY": manager_id, "X-AEGIS-DEVICE": "mgr-dev"}
        h_fin = {"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": "fin-dev"}

        # 2. CREATE PR
        print("[1] Creating Purchase Request (Order Initiation)...")
        items = [{"id": "ro-001", "qty": 5, "est_price": 10000}]
        res = await client.post("/commerce/orders/create", json={"items": items, "amount": 50000}, headers=h_mgr)
        order_id = res.json()["id"]
        print(f"    Order Created: {order_id} (Status: {res.json()['status']})")

        # 3. APPROVAL (Single for 50k)
        print("[2] Approving Order...")
        res = await client.post("/commerce/orders/approve", params={"order_id": order_id}, headers=h_mgr)
        print(f"    Order Status: {res.json()['status']}")

        # 4. LIFECYCLE (Dispatch -> Deliver)
        print("[3] Simulating Dispatch & Delivery...")
        await client.post("/commerce/orders/dispatch", params={"order_id": order_id}, headers=h_mgr)
        res = await client.post("/commerce/orders/deliver", params={"order_id": order_id}, headers=h_mgr)
        print(f"    Order Status: {res.json()['status']}")

        # 5. INVOICE (MIRA Calculation)
        print("[4] Generating Final Invoice (MIRA Tax)...")
        res = await client.post("/commerce/orders/invoice", params={"order_id": order_id}, headers=h_fin)
        pricing = res.json()["pricing"]
        print(f"    Total with TGST: {pricing['total']} MVR")

        # 6. SETTLEMENT (Fail without National ID Verified)
        print("[5] Attempting Settlement (Expected Fail - No NatID verified)...")
        res = await client.post("/commerce/orders/settle", params={"order_id": order_id}, headers=h_fin)
        print(f"    Result: {res.status_code} ({res.json().get('detail')})")

        # 7. SETTLEMENT (Success with verified context)
        # Note: In our current simple execution guard, we check actor_context.get("national_id_verified")
        # In this simulation, we simulate the verification by updating the request headers
        # (in a real system this would be in the profile db)
        print("[6] Attempting Settlement (Success with Verified Identity)...")
        h_fin_verified = {**h_fin, "X-AEGIS-VERIFIED": "true"}
        res = await client.post("/commerce/orders/settle", params={"order_id": order_id}, headers=h_fin_verified)
        print(f"    Settlement Status: {res.json()['status']}")

        # 8. AUDIT CHECK
        print("[7] Verifying SHADOW Audit Trail...")
        res = await client.get("/health")
        print(f"    Integrity: {'PASSED' if res.json()['integrity'] else 'FAILED'}")

    print("-" * 60)
    print("✅ BRIDGE SIMULATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(simulate_bridge())
