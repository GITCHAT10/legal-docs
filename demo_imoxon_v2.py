import httpx
import asyncio
import os

async def run_v2_demo():
    print("🚀 STARTING iMOXON SOVEREIGN ENGINE DEMO (V2)")
    print("-" * 40)

    os.environ["NEXGEN_SECRET"] = "mnos-sovereign-secret"

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Onboard Local User
        print("[1] Onboarding Local User Moosa...")
        moosa_res = await client.post("/auth/onboard", json={
            "name": "Moosa",
            "role": "LOCAL_USER",
            "device_id": "moosa-phone-101"
        })
        moosa = moosa_res.json()
        moosa_did = moosa["did"]
        print(f"    Success: DID={moosa_did}")

        # 2. Test Local-Only Gate (Tourist Try)
        print("[2] Testing Tourist Block (Fail-Closed)...")
        tourist_res = await client.post("/auth/onboard", json={
            "name": "John Tourist",
            "role": "TOURIST_USER"
        })
        print(f"    Tourist Status: {tourist_res.status_code} (Expected 400 because Aegis raises Exception)")

        # 3. Transport Ride Flow
        print("[3] Requesting Local Taxi (Transport Engine)...")
        ride_res = await client.post("/transport/ride", json={
            "user_id": moosa_did,
            "device_id": "moosa-phone-101",
            "role": "LOCAL_USER",
            "pickup": "Male City",
            "destination": "Airport"
        })
        ride = ride_res.json()
        print(f"    Ride Status: {ride['status']} | Fare: {ride['ride']['fare']['total']} MVR")

        # 4. Logistics Flow
        print("[4] Creating Shipment (Logistics Engine)...")
        ship_res = await client.post("/logistics/ship", params={
            "sender_id": moosa_did,
            "origin": "Male",
            "destination": "Gan",
            "items": ["Medicine", "Food"]
        })
        shipment = ship_res.json()
        print(f"    Shipment ID: {shipment['shipment']['shipment_id']}")

        # 5. iSKY HMS Commission Flow
        print("[5] iSKY Cloud HMS Activation...")
        isky_res = await client.post("/isky/activate", params={"operator_id": "operator_island_4"})
        isky = isky_res.json()
        print(f"    iSKY Activation Status: {isky['status']} | Setup Fee: ${isky['activation']['setup_fee']}")

        # 6. Final Integrity
        print("[6] Final Integrity Audit (SHADOW)...")
        health_res = await client.get("/health")
        health = health_res.json()
        print(f"    SHADOW Integrity: {health['shadow_integrity']}")

    print("-" * 40)
    print("✅ iMOXON V2 DEMO COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_v2_demo())
