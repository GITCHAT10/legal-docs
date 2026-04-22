import httpx
import asyncio
import os
import time

async def run_full_demo():
    print("🚀 STARTING iMOXON FULL SYSTEM DEMO")
    print("-" * 40)

    os.environ["NEXGEN_SECRET"] = "mnos-production-secret"

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Onboard Buyer
        print("[1] Onboarding Buyer...")
        buyer = (await client.post("/onboard/user", json={"name": "Moosa", "email": "moosa@island.mv"})).json()
        token = buyer["token"]
        print(f"    DID: {buyer['did']}")

        # 2. Onboard Merchant
        print("[2] Onboarding Merchant...")
        merchant = (await client.post("/onboard/merchant", json={
            "business_name": "Maldives Curio",
            "registration_number": "MV-001",
            "bank_account": "BML-1234"
        })).json()
        merchant_did = merchant["did"]
        print(f"    DID: {merchant_did}")

        # 3. Create Listing
        print("[3] Creating Listing...")
        listing = (await client.post("/listings", json={
            "title": "Traditional Dhoni Model",
            "category": "retail",
            "price": 1200.0,
            "stock": 5,
            "merchant_id": merchant_did
        })).json()
        lid = listing["listing_id"]
        print(f"    Listing ID: {lid}")

        # 4. Checkout (Retail)
        print("[4] Executing Checkout (Retail)...")
        order = (await client.post("/checkout", json={
            "user_token": token,
            "listing_id": lid,
            "coupon_code": "SAVE10"
        })).json()
        print(f"    Total with Taxes: ${order['order']['pricing']['total']}")

        # 5. Tourism Booking
        print("[5] Tourism Booking...")
        tourism = (await client.post("/tourism/book", json={
            "user_token": token,
            "experience_type": "Sunset Cruise",
            "pax": 4,
            "nights": 0,
            "base_price_per_pax": 75.0
        })).json()
        print(f"    Tourism Total: ${tourism['booking']['pricing']['total']}")

        # 6. Installments
        print("[6] Calculating Installments...")
        inst = (await client.post("/installments", json={"total": 5000.0, "months": 12})).json()
        print(f"    Monthly Payment: ${inst['schedule'][0]['amount']}")

        # 7. Asset Listing & Exchange
        print("[7] Asset Exchange...")
        asset = (await client.post("/assets/list", json={
            "merchant_id": merchant_did,
            "asset_name": "Guest House Share",
            "price": 25000.0
        })).json()
        aid = asset["asset"]["asset_id"]

        transfer = (await client.post("/assets/transfer", json={
            "asset_id": aid,
            "buyer_token": token,
            "amount": 25000.0
        })).json()
        print(f"    Asset Transfer Finalized: {transfer['transfer_finalized']}")

        # 8. Supply Restock
        print("[8] Supply Engine Trigger...")
        sup = (await client.post(f"/supply/restock?merchant_id={merchant_did}&listing_id={lid}&amount=10")).json()
        print(f"    Supply Status: {sup['supply_event']['status']}")

        # 9. Payout
        print("[9] Merchant Payout...")
        pay = (await client.post(f"/payout?merchant_id={merchant_did}&amount=5000.0")).json()
        print(f"    Net Payout: ${pay['payout']['net']}")

        # 10. Fail Closed Test
        print("[10] Testing Fail-Closed (Invalid Token)...")
        fail = await client.post("/checkout", json={
            "user_token": "INVALID_TOKEN",
            "listing_id": lid
        })
        print(f"     Status Code: {fail.status_code} (Expected 401)")

        # 11. Integrity Check
        print("[11] Final Integrity Audit...")
        health = (await client.get("/health")).json()
        print(f"     SHADOW Integrity: {health['integrity']}")

    print("-" * 40)
    print("✅ iMOXON DEMO COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_full_demo())
