import sys
import os
from decimal import Decimal

# Ensure we can import from mnos
sys.path.append(os.getcwd())

from main import app, identity_core, guard, hospitality, iluvia_orchestrator, shadow_core, identity_gateway

def simulate():
    print("🚀 STARTING SALA PILOT DAY 1: SCENARIO A")

    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    # 1. Setup Actor & Property
    with guard.sovereign_context(SYSTEM_CTX):
        staff_id = identity_core.create_profile({"full_name": "SALA Front Desk", "profile_type": "staff"})
        device_id = identity_core.bind_device(staff_id, {"fingerprint": "sala-tablet-01"})
        identity_core.verify_identity(staff_id, "mig-onboarding")

        # Register SALA Guesthouse
        prop = hospitality.register_property(SYSTEM_CTX, {
            "name": "SALA Beach House",
            "location": "Omadhoo",
            "base_rate": 85.0,
            "type": "GUESTHOUSE"
        })

    staff_ctx = {
        "identity_id": staff_id,
        "device_id": device_id,
        "role": "staff",
        "realm": "API_DIRECT"
    }

    print(f"✔ Property Registered: {prop['id']}")

    # 2. Create Booking
    print("📅 Creating Booking...")
    booking = hospitality.book_stay(staff_ctx, {
        "property_id": prop["id"],
        "nights": 2,
        "amenities": ["aircon", "wifi_premium"]
    })
    print(f"✔ Booking Confirmed: {booking['booking_id']} | Total: {booking['pricing']['total']} MVR")

    # 3. Reality Check: Check-in (Digital -> Physical Signal)
    print("🆔 Executing Reality Check (Check-in)...")
    iluvia_orchestrator.set_order_state(booking["booking_id"], "EXECUTION_PENDING", "HOSPITALITY")

    signal = {"type": "BIOMETRIC_CHECKIN", "valid": True}
    success = guard.execute_sovereign_action(
        "bubble.execution.confirm",
        staff_ctx,
        iluvia_orchestrator.confirm_real_world,
        booking["booking_id"], signal
    )
    print(f"✔ Check-in Verified via ILUVIA: {success}")

    # 4. ORCA Dashboard Verification
    print("📊 Verifying ORCA Dashboard...")
    # Add session for ORCA
    identity_gateway.sessions["SALA-DASH-SESSION"] = staff_ctx

    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/orca/dashboard/summary", headers={"X-AEGIS-SESSION": "SALA-DASH-SESSION"})
    if response.status_code == 200:
        data = response.json()
        metrics = data["metrics"]
        print(f"✔ Dashboard Data Found: Revenue={metrics['total_revenue_mvr']} MVR, Bookings={metrics['total_bookings_today']}")
        if metrics['total_revenue_mvr'] > 0:
            print("✔ FINANCIAL SYNC: OK")
        else:
            print("❌ FINANCIAL SYNC: Revenue is 0. Check logic.")
    else:
        print(f"❌ Dashboard Failed: {response.status_code} {response.text}")

    print("🏁 SCENARIO A COMPLETE")

if __name__ == "__main__":
    simulate()
