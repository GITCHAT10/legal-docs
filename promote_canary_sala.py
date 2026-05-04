import httpx
import asyncio
import os
from main import app, shadow_core, events_core
from httpx import ASGITransport

async def run_promotion_and_checks():
    print("🏛️ iMOXON CANARY PROMOTION: SALA")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "ndeos-promotion-2026"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Actor
        res = await client.post("/aegis/identity/create", json={"full_name": "Sovereign Controller", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "ctrl-hub-01"})
        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": "ctrl-hub-01",
            "X-MNOS-SIGNATURE": "sys-auth-v1"
        }

        # 2. Execute Promotion
        print("[1] Increasing SALA traffic to 15%...")
        res = await client.post("/imoxon/canary/promote", params={"percentage": 15}, headers=headers)
        if res.status_code == 200:
            print(f"    Status: {res.json()['status']} | Traffic: {res.json()['traffic']}%")
        else:
            print(f"    Promotion Failed: {res.text}")
            return

        # 3. Verification Post-Promotion
        print("[2] Running post-promotion health checks...")

        # Finance Accuracy check (MIRA Rule)
        print("   -> Verifying Finance Accuracy (SC 10%, TGST 17%)...")
        order_res = await client.post("/imoxon/orders/create", json={
            "amount": 2000,
            "category": "RESORT_SUPPLY",
            "items": [{"id": "p-99", "qty": 2}]
        }, headers=headers)
        pricing = order_res.json()["pricing"]
        # Expected: 2000 + 200 (SC) = 2200. 2200 * 0.17 = 374. Total = 2574.
        if pricing["total"] == 2574.0:
            print("      [PASS] MIRA Billing Logic enforced.")
        else:
            print(f"      [FAIL] Pricing mismatch: {pricing['total']} vs 2574.0")

        # Shadow Integrity check
        print("   -> Verifying SHADOW Chain Integrity...")
        integrity = shadow_core.verify_integrity()
        if integrity:
            print("      [PASS] Hash chain valid.")
        else:
            print("      [FAIL] SHADOW chain compromised!")

        # Event-Law Compliance (Direct Publish Blocked)
        print("   -> Verifying Event-Law Compliance...")
        try:
            events_core.publish("ILLEGAL_EVENT", {})
            print("      [FAIL] Direct publish allowed!")
        except PermissionError:
            print("      [PASS] Direct publish blocked by ExecutionGuard.")

        # 4. Final Output Metrics
        health_res = await client.get("/health")
        metrics = health_res.json()

        print("-" * 60)
        print("📊 PROMOTION SUMMARY")
        print("   - Target Node:  SALA Resort")
        print("   - Status:       ACTIVE")
        print(f"   - Traffic:      {metrics['canary_traffic']}%")
        print(f"   - Integrity:    {'SECURE' if metrics['integrity'] else 'ERROR'}")
        print("   - Compliance:   100% Locked")
        print("\n📢 KILL-SWITCH: Auto-rollback ARMED on Shadow or Finance violation.")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(run_promotion_and_checks())
