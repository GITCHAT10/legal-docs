import httpx
import asyncio
import os
import json
import random
from main import app, shadow_core

async def simulate_mig_shield_mnos():
    print("🚀 STARTING MIG SHIELD MNOS INTEGRATED SIMULATION")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "mig-shield-2026"
    from httpx import ASGITransport
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Actor (MIG Admin)
        print("[1] Initializing Sovereign Identity (MIG Admin)...")
        res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "MIG Admin", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "mig-dev-01"})
        device_id = res.json()["device_id"]

        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
        }

        # 2. Trigger Missions
        print("[2] Dispatching Emergency Response Missions...")
        incident_types = ["DROWNING", "FIRE", "MEDICAL"]
        for i in range(5):
            inc_type = random.choice(incident_types)
            payload = {
                "type": inc_type,
                "severity": 4, # CRITICAL
                "location": [random.uniform(0, 8), random.uniform(0, 8)]
            }
            res = await client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=headers)
            if res.status_code == 200:
                print(f"    Mission {i+1}: DISPATCHED | Drone: {res.json()['drone_id']}")
            else:
                print(f"    Mission {i+1}: FAILED | {res.json().get('detail', 'Unknown Error')}")

        # 3. Validate ORCA Metrics
        print("[3] Fetching ORCA Dashboard Metrics...")
        res = await client.get("/imoxon/orca/metrics", headers=headers)
        metrics = res.json()
        print(f"    ORCA Status: {metrics.get('status', 'N/A')} | Success Rate: {metrics.get('success_rate', 0)*100:.1f}%")

        # 4. Generate 3-30-3 KPI Report
        print("[4] Generating 3-30-3 KPI Validation Report...")
        res = await client.get("/imoxon/mig-shield/kpis", headers=headers)
        kpis = res.json()

        print("\n" + "="*55)
        print("📊 MIG SHIELD DIGITAL TWIN — 3-30-3 KPI REPORT")
        print("="*55)
        print(f"⚡ Dispatch Latency: {kpis['dispatch_latency_avg']:.2f}s  (Target <3s)  {'✅' if kpis['dispatch_latency_avg'] < 3 else '❌'}")
        print(f"🚁 Airborne Time:   {kpis['airborne_time_min']:.2f}s  (Target <30s) {'✅' if kpis['airborne_time_min'] < 30 else '⏳'}")
        print(f"✅ Success Rate:    {kpis['success_rate']:.1f}%")
        print(f"🔗 SHADOW Integrity: {'VERIFIED ✅' if kpis['shadow_integrity'] else 'COMPROMISED ❌'}")
        print("="*55 + "\n")

    print("-" * 60)
    print("✅ MIG SHIELD MNOS SIMULATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(simulate_mig_shield_mnos())
