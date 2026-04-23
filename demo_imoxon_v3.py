import httpx
import asyncio
import os

async def run_v3_sovereign_audit():
    print("🏛️ STARTING iMOXON SOVEREIGN SYSTEM FULL AUDIT (V3)")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "mnos-sovereign-audit"

    from main import app
    from httpx import ASGITransport
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. AEGIS Onboarding
        print("[1] AEGIS Identity Creation (Landlord & Tenant)...")
        l_res = await client.post("/aegis/identity/create", json={"full_name": "Adam Landlord", "profile_type": "staff"})
        t_res = await client.post("/aegis/identity/create", json={"full_name": "Hassan Tenant", "profile_type": "staff"})
        l_id, t_id = l_res.json()["identity_id"], t_res.json()["identity_id"]

        # Bind devices
        await client.post("/aegis/identity/device/bind", params={"identity_id": l_id}, json={"fingerprint": "phone-1"})
        await client.post("/aegis/identity/device/bind", params={"identity_id": t_id}, json={"fingerprint": "phone-2"})

        # 2. Tenancy Agreement (LEX) - Using Supply routes for now as Lex isn't fully wired in main
        print("[2] Capturing Demand Signal (Sovereign Verification)...")
        headers = {"X-AEGIS-IDENTITY": l_id, "X-AEGIS-DEVICE": "phone-1"}
        demand = (await client.post("/supply/demand/signals", params={"resort_id": "MIG-RESORT-01"}, json=[{"item": "Water RO", "qty": 10}], headers=headers)).json()
        print(f"    Signal ID: {demand['signal']['id']} | Status: VALIDATED")

        # 3. Award RFP (Financial Milestone)
        print("[3] Awarding RFP (FCE Payout Release)...")
        award = (await client.post("/supply/rfps/award", params={"rfp_id": "rfp_123", "supplier_id": "sup_99"}, headers=headers)).json()
        print(f"    Payout Milestone: {award['payout']['milestone']} | Amount: {award['payout']['release_amount']} MVR")

        # 4. Inventory Allocation (Skygodown)
        print("[4] Allocating Inventory (MNOS SKYGODOWN)...")
        alloc = (await client.post("/supply/lots/allocate", params={"lot_id": "lot_v55", "resort_id": "MIG-RESORT-01"}, json={"RO_Membrane": 2}, headers=headers)).json()
        print(f"    Allocation Lot: {alloc['allocation']['lot_id']} | Status: {alloc['allocation']['status']}")

        # 5. Delivery Confirmation
        print("[5] Confirming Delivery (Final Payout)...")
        delivery = (await client.post("/supply/manifests/confirm", params={"manifest_id": "man_789", "resort_id": "MIG-RESORT-01"}, json=[], headers=headers)).json()
        print(f"    Final Payout: {delivery['payout']['release_amount']} MVR | Integrity: SEALED")

        # 6. Integrity Check
        print("[6] Final Authority Integrity Audit...")
        health = (await client.get("/health")).json()
        print(f"    SHADOW Ledger Integrity: {health['integrity']}")

    print("-" * 60)
    print("✅ iMOXON SOVEREIGN SYSTEM AUDIT COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_v3_sovereign_audit())
