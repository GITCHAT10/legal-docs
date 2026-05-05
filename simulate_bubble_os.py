import httpx
import asyncio
import os
from main import app
from httpx import ASGITransport

async def simulate_bubble_os():
    print("🚀 STARTING BUBBLE OS SUPER APP SIMULATION")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "bubble-sim-2026"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup
        res = await client.post("/aegis/identity/create", json={"full_name": "Adam User", "profile_type": "user"})
        actor_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "adam-phone-01"})
        headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "adam-phone-01"}

        # 2. Chat to Transaction Simulation
        print("[1] Simulating Chat Intent: 'Order 20 bags of rice'...")
        res = await client.post("/bubble/chat/message", params={"message": "Order 20 bags of rice"}, headers=headers)
        card = res.json()
        print(f"    System Response: {card['title']}")
        print(f"    Calculated Price: {card['data']['price']} {card['data']['currency']}")
        print(f"    Next Action: {card['actions'][0]['label']}")

        # 3. Mini App Registration
        print("[2] Registering Mini App: 'Transport App'...")
        manifest = {
            "app_id": "transport_app",
            "permissions": ["order.create"],
            "api_scope": "imoxon.transport"
        }
        await client.post("/bubble/sdk/register", json=manifest)
        print("    Mini App Registered in Sandbox.")

        # 4. Wallet Check
        print("[3] Checking Wallet OS Balance...")
        res = await client.post("/bubble/wallet/balance", headers=headers)
        print(f"    Balance: {res.json()['balance']} {res.json()['currency']}")

    print("-" * 60)
    print("✅ BUBBLE OS SIMULATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(simulate_bubble_os())
