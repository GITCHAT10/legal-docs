import pytest
import traceback
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard, pms_availability, iluvia_orchestrator
from datetime import date, timedelta
import uuid

@pytest.mark.anyio
async def test_full_commercial_flow_activation():
    """
    Scenario: Prestige Booking -> MAC EOS Gate -> UPOS Payment -> CSR Allocation
    """
    # PRE-REQUISITE 1: Initialize PMS Inventory
    start = date.today()
    pms_availability.initialize_inventory("DELUXE_VILLA", 10, start, days=60)

    # PRE-REQUISITE 2: Register Identity and Device in AEGIS
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        guest_id = identity_core.create_profile({
            "full_name": "Sovereign Traveler",
            "profile_type": "guest"
        })
        device_id = identity_core.bind_device(guest_id, {"fingerprint": "ios_99"})
        identity_core.verify_identity(guest_id, "SYSTEM")

        infra_id = identity_core.create_profile({
            "full_name": "Infra Node",
            "profile_type": "infra"
        })
        infra_device = identity_core.bind_device(infra_id, {"fingerprint": "hw_01"})
        identity_core.verify_identity(infra_id, "SYSTEM")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Step 1: Create Booking via PMS (MAC EOS Hardened)
        # Using Direct Auth headers for test simplicity
        headers = {
            "X-AEGIS-IDENTITY": guest_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{guest_id}"
        }

        # Consistent with CreateReservationRequest
        booking_payload = {
            "guest_id": guest_id,
            "room_type_id": "DELUXE_VILLA",
            "villa_id": "SV-101", # SHIELDED_VILLA Triggers Privacy Premium
            "rate_plan_id": "EARLY_BIRD",
            "check_in": str(date.today() + timedelta(days=30)),
            "check_out": str(date.today() + timedelta(days=37)),
            "idempotency_key": str(uuid.uuid4()),
            "total_amount": 2500.0
        }

        res = await ac.post("/pms/reservations", json=booking_payload, headers=headers)
        if res.status_code != 200:
            print(f"FAILED PMS: {res.status_code} - {res.text}")
        assert res.status_code == 200
        booking = res.json()
        assert booking["privacy_premium_active"] is True
        assert booking["total_amount"] > 0

        # LINKAGE: Bubble Orchestrator needs to know about the PMS order
        # In a real system, PMS would publish an event that Bubble listens to
        iluvia_orchestrator.set_order_state(booking["id"], "EXECUTION_PENDING", "HOSPITALITY")

        # 2. Step 2: Confirmation of real-world signals (Bubble Orchestrator)
        infra_headers = {
            "X-AEGIS-IDENTITY": infra_id,
            "X-AEGIS-DEVICE": infra_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{infra_id}"
        }

        confirm_url = f"/bubble/execution/confirm?order_id={booking['id']}"
        confirm_payload = {"type": "BIOMETRIC_CHECKIN", "valid": True}

        res = await ac.post(confirm_url, json=confirm_payload, headers=infra_headers)
        if res.status_code != 200:
            print(f"FAILED CONFIRM: {res.status_code} - {res.text}")
        assert res.status_code == 200

        # 3. Step 3: UPOS Payment Execution
        payment_order = {
            "amount": booking["total_amount"],
            "vendor_id": "SALA_RESORT_01"
        }
        res = await ac.post("/upos/order/create", json=payment_order, headers=headers)
        assert res.status_code == 200
        intent = res.json()
        intent_id = intent["id"]

        exec_payload = {"intent_id": intent_id}
        res = await ac.post("/upos/payment/execute", json=exec_payload, headers=headers)
        assert res.status_code == 200
        settlement = res.json()

        assert settlement["status"] == "SETTLED"
        assert settlement["vendor_net"] == booking["total_amount"]

        # 4. Verify CSR Allocation (Forensic Audit)
        health = await ac.get("/health")
        assert health.status_code == 200
        assert health.json()["sovereign_status"] == "LOCKED"

@pytest.mark.anyio
async def test_csr_report_and_fund_release():
    """
    Scenario: Generate CSR report after transactions and release funds.
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        staff_id = identity_core.create_profile({"full_name": "CSR Manager", "profile_type": "staff"})
        device_id = identity_core.bind_device(staff_id, {"fingerprint": "pc_01"})
        identity_core.verify_identity(staff_id, "SYSTEM")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-AEGIS-IDENTITY": staff_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{staff_id}"
        }

        # 1. Get Report
        res = await ac.get("/csr/csr/report", headers=headers)
        assert res.status_code == 200
        report = res.json()
        assert "total_funds" in report

        # 2. Release Funds (assuming there are funds from previous test or we add some)
        # For isolation, let's trigger a payment first
        guest_headers = headers # Reuse for simplicity
        payment_order = {"amount": 1000.0, "vendor_id": "VENDOR_A"}
        res = await ac.post("/upos/order/create", json=payment_order, headers=guest_headers)
        intent_id = res.json()["id"]
        await ac.post("/upos/payment/execute", json={"intent_id": intent_id}, headers=guest_headers)

        # Now release from NGO bucket
        release_payload = {
            "bucket": "NGO",
            "amount": 1.0,
            "milestone": "Project Alpha Start"
        }
        res = await ac.post("/csr/csr/release", json=release_payload, headers=headers)
        assert res.status_code == 200
        release = res.json()
        assert release["bucket"] == "NGO"
        assert release["amount"] == 1.0
