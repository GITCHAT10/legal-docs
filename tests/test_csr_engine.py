import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, guard, identity_core, upos_ledger, upos_engine, csr_engine
from decimal import Decimal

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def reset_state():
    from main import gateway, shield_edge
    gateway.rate_limits = {}
    shield_edge.rate_store = {}
    upos_ledger.balances = {}
    upos_engine.intents = {}
    csr_engine.csr_pool = {k: Decimal("0.00") for k in csr_engine.csr_pool}
    csr_engine.allocation_history = []
    yield

@pytest.fixture
def auth_headers():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        uid = identity_core.create_profile({"full_name": "SALA Guest", "profile_type": "guest"})
        did = identity_core.bind_device(uid, {"fingerprint": "guest-dev-99"})
        identity_core.verify_identity(uid, "system")
        upos_ledger.post_transaction(uid, Decimal("10000.00"), "MVR", "SETTLEMENT_INFLOW", "INIT")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_csr_engine_trigger_on_payment(auth_headers):
    """CSR Engine Implementation: Trigger on completed payment."""
    vendor_id = "VEND-1"

    # 1. Create Order (10,000 MVR Base)
    order_payload = {"amount": 10000.0, "vendor_id": vendor_id}
    resp1 = client.post("/upos/order/create", json=order_payload, headers=auth_headers)
    intent_id = resp1.json()["id"]

    # 2. Execute Payment
    # This should trigger CSR calculation:
    # profit = 10000 * 0.30 = 3000
    # csr = 3000 * 1.5% = 45.0
    client.post("/upos/payment/execute", json={"intent_id": intent_id}, headers=auth_headers)

    # 3. Verify CSR Report
    resp2 = client.get("/csr/csr/report", headers=auth_headers)
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["total_funds"] == 45.0

    # Verify Split: NGO = 25% of 45 = 11.25
    assert data["bucket_allocation"]["NGO"] == 11.25
    assert data["bucket_allocation"]["EDUCATION"] == 9.0
    assert data["bucket_allocation"]["MEDICAL"] == 9.0
    assert data["bucket_allocation"]["FOOD_SAFETY"] == 6.75
    assert data["bucket_allocation"]["CHILD_SAFETY"] == 9.0

    # 4. Verify Audit Trail
    events = [b["event_type"] for b in shadow_core.chain]
    assert "csr.engine.allocate.completed" in events

def test_csr_fund_release(auth_headers):
    """CSR Engine Disbursement: Release funds on milestone."""
    # 1. Setup funds via payment
    vendor_id = "VEND-1"
    order_payload = {"amount": 10000.0, "vendor_id": vendor_id}
    resp1 = client.post("/upos/order/create", json=order_payload, headers=auth_headers)
    client.post("/upos/payment/execute", json={"intent_id": resp1.json()["id"]}, headers=auth_headers)

    # 2. Release funds from NGO bucket (initially 11.25)
    release_payload = {"bucket": "NGO", "amount": 5.0, "milestone": "PHASE_1_COMPLETE"}
    resp = client.post("/csr/csr/release", json=release_payload, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 5.0

    # 3. Verify balance reduction
    resp2 = client.get("/csr/csr/report", headers=auth_headers)
    assert resp2.json()["bucket_allocation"]["NGO"] == 6.25

def test_csr_engine_rejects_negative_profit(auth_headers):
    """CSR Logic: Reject if profit <= 0 (Simulated via zero base)"""
    # Engines block zero/negative amounts at intent stage, but let's check logic bypass
    res = csr_engine.calculate_and_allocate(auth_headers, {"profit": -100})
    assert res["status"] == "SKIPPED"
