import httpx
import asyncio
from imoxon_national.ai_engine.role_detection import RoleDetectionAI
from imoxon_national.core_fastapi.main import app
from httpx import ASGITransport

async def simulate_national_deos():
    print("🏛️ IMOXON NATIONAL DIGITAL TWIN SIMULATION")
    print("-" * 60)

    transport = ASGITransport(app=app)
    ai_role = RoleDetectionAI()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Role Detection (Farmer)
        print("[1] AI Role Detection...")
        user_signals = {"tx_type": "crop_sales", "frequency": 12}
        profile = ai_role.predict_role("FARMER-01", user_signals)
        print(f"    Detected Role: {profile['primary_role']} (Confidence: {profile['confidence']})")
        print(f"    UI Adaptation: {profile['adaptive_ui']}")

        # 2. Marketplace: Farmer -> Hotel
        print("[2] Executing Cross-Role Transaction (Farmer -> Hotel)...")
        # List product (Farmer)
        res = await client.post("/marketplace/list", json={"role": "FARMER", "name": "Organic Tomatoes", "price": 22.0, "unit": "kg"})
        pid = res.json()["id"]

        # Purchase product (Hotel)
        res = await client.post("/marketplace/purchase", json={"product_id": pid, "quantity": 100, "buyer_id": "HOTEL-99"})
        order = res.json()
        print(f"    Order Settled: {order['total']} MVR (MIRA Enforced)")

        # 3. National Dashboard Check
        print("[3] Fetching Ministry Economic Visibility...")
        from imoxon_national.core_fastapi.dashboard import MinistryDashboard
        dash = MinistryDashboard(None)
        status = dash.get_national_status()
        print(f"    National GDP Flow: {status['gdp_flow']}")

        alerts = dash.get_alerts()
        for alert in alerts:
            print(f"    🚨 ALERT: {alert['type']} on {alert.get('item')}")

    print("-" * 60)
    print("✅ NATIONAL DIGITAL TWIN SIMULATION SUCCESS")

if __name__ == "__main__":
    asyncio.run(simulate_national_deos())
