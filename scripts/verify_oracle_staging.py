import httpx
import asyncio
import os

async def verify_oracle():
    print("--- PRESTIGE ORACLE: Verification Script ---")

    # Use local uvicorn since docker isn't available in sandbox
    # but we simulate the staging URL
    base_url = "http://127.0.0.1:8000"
    headers = {"X-PRESTIGE-API-KEY": "staging-dev-key-777"}

    print("\n[1] Testing /predict-success...")
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        try:
            resp = await client.post("/predict-success", json={
                "candidate_pillars": {"haccp": 85, "iso": 80, "unesco": 75, "michelin": 90},
                "role_weights": {"haccp": 0.3, "iso": 0.25, "unesco": 0.2, "michelin": 0.25},
                "manager_tier": 0.8,
                "resort_complexity": 0.6,
                "location_readiness": 0.9
            })
            print(f"Status: {resp.status_code}")
            print(f"Result: {resp.json()}")
        except Exception as e:
            print(f"Error: {e}")

        print("\n[2] Testing /shadow-update...")
        resp = await client.post("/shadow-update", json={
            "current_beliefs": {
                "haccp": {"alpha": 5, "beta_dist": 1}
            },
            "event_pillar": "haccp",
            "event_outcome": "positive",
            "event_weight": 2.0
        })
        print(f"Status: {resp.status_code}")
        print(f"Result: {resp.json()}")

        print("\n[3] Testing /evaluate-deployment...")
        resp = await client.post("/evaluate-deployment", json={
            "candidate_beliefs": {
                "haccp": {"mean": 0.9, "variance": 0.01}
            },
            "role_requirements": {"haccp": 0.8},
            "uncertainty_tolerance": 0.85
        })
        print(f"Status: {resp.status_code}")
        print(f"Result: {resp.json()}")

        print("\n[4] Testing /optimize-exmail-offer...")
        resp = await client.post("/optimize-exmail-offer", json={
            "segment": "GCC",
            "season": "peak",
            "inventory_level": 0.8
        })
        print(f"Status: {resp.status_code}")
        print(f"Result: {resp.json()}")

if __name__ == "__main__":
    # To run this, you need the app running in the background:
    # PRESTIGE_API_KEY=staging-dev-key-777 uvicorn prestige_oracle.app:app --reload
    asyncio.run(verify_oracle())
