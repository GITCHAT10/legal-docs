import asyncio
import json
import uuid
import random
from decimal import Decimal
from datetime import datetime, UTC
import httpx

class LiveQuoteMachineSim:
    """
    Simulates the Live Quote Machine: <15 min response time.
    Processes incoming inquiries and generates MIRA-compliant quotes.
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.processed_quotes = []

    async def simulate_inquiry(self, agent_id: str, resort_id: str, net_amount: float):
        """Processes a single incoming inquiry."""
        print(f"📥 Inquiry received from {agent_id} for {resort_id}...")

        async with httpx.AsyncClient() as client:
            # 1. Setup Auth
            res = await client.post(f"{self.base_url}/imoxon/aegis/identity/create", json={"full_name": agent_id, "profile_type": "dmc_ta_staff"})
            identity_id = res.json()["identity_id"]
            res = await client.post(f"{self.base_url}/imoxon/aegis/identity/device/bind?identity_id={identity_id}", json={})
            device_id = res.json()["device_id"]

            headers = {
                "X-AEGIS-IDENTITY": identity_id,
                "X-AEGIS-DEVICE": device_id,
                "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
            }

            # 2. Call Pricing Logic (via procurement flow as proxy for quote)
            payload = {
                "items": [f"{resort_id} Villa Reservation"],
                "amount": net_amount,
                "product_type": "PACKAGE",
                "tax_type": "TOURISM_STANDARD",
                "trace_id": f"QT-{uuid.uuid4().hex[:6].upper()}"
            }

            start_time = datetime.now(UTC)
            # Step 1: Create PR
            res = await client.post(f"{self.base_url}/imoxon/orders/create", json=payload, headers=headers)
            order_id = res.json()["id"]

            # Step 2: Invoice (to get pricing)
            res = await client.post(f"{self.base_url}/imoxon/orders/invoice?order_id={order_id}", headers=headers)
            end_time = datetime.now(UTC)

            if res.status_code == 200:
                response_time_sec = (end_time - start_time).total_seconds()
                quote_data = res.json()
                # In procurement invoice, pricing is at top level
                print(f"✅ Quote generated for {agent_id} in {response_time_sec:.2f}s")
                self.processed_quotes.append(quote_data)
            else:
                print(f"❌ Quote failed: {res.text}")

    async def run_batch(self, count: int = 10):
        resorts = ["KUREDU", "MEERU", "BAROS", "VILAMENDHOO", "VELIGANDU"]
        agents = ["EliteTravel_RU", "GlobalWings_AE", "SkyHolidays_DE", "NexusTravel_CIS", "MaldiveExperts_UK"]

        # Sequentially to avoid overwhelming small sandbox server
        for i in range(count):
            agent = random.choice(agents)
            resort = random.choice(resorts)
            net = random.randint(1500, 8000)
            await self.simulate_inquiry(f"{agent}_{i}", resort, net)

        print(f"\n📊 Total Quotes Processed: {len(self.processed_quotes)}")

async def main():
    sim = LiveQuoteMachineSim()
    # Ensure server is running before this
    await sim.run_batch(30)

if __name__ == "__main__":
    asyncio.run(main())
