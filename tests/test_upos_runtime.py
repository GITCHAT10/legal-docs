import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, guard, identity_core, upos_ledger, upos_engine, events_core
from decimal import Decimal

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def reset_state():
    from main import gateway, shield_edge
    gateway.rate_limits = {}
    shield_edge.rate_store = {}
    upos_ledger.balances = {}
    upos_engine.intents = {}
    yield

@pytest.fixture
def auth_headers():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        uid = identity_core.create_profile({"full_name": "SALA Guest", "profile_type": "guest"})
        did = identity_core.bind_device(uid, {"fingerprint": "guest-dev-99"})
        identity_core.verify_identity(uid, "system")

        # Initial Balance
        upos_ledger.post_transaction(uid, Decimal("5000.00"), "MVR", "SETTLEMENT_INFLOW", "INIT")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_full_upos_payment_lifecycle(auth_headers):
    """Production Runtime Activation: ORDER -> INTENT -> EXECUTE -> SPLIT -> AUDIT"""
    vendor_id = "VEND-CAFE-01"

    # 1. Create Order (Intent)
    order_payload = {"amount": 1000.0, "vendor_id": vendor_id}
    resp1 = client.post("/upos/order/create", json=order_payload, headers=auth_headers)
    if resp1.status_code != 200:
        print(f"DEBUG: Order create failed: {resp1.json()}")
    assert resp1.status_code == 200
    intent_id = resp1.json()["id"]
    assert resp1.json()["total_payable"] == 1287.0

    # 2. Execute Payment
    pay_payload = {"intent_id": intent_id, "payment_method": "QR_PAY"}
    resp2 = client.post("/upos/payment/execute", json=pay_payload, headers=auth_headers)
    if resp2.status_code != 200:
        print(f"DEBUG: Payment execute failed: {resp2.json()}")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "SETTLED"
    assert resp2.json()["vendor_net"] == 1000.0

    # 3. Verify Wallet Balances
    resp3 = client.get("/upos/wallet/balance", headers=auth_headers)
    assert resp3.json()["balance"] == 3713.0

    # Vendor: 1000 (Net)
    balance_vend = upos_ledger.get_balance(vendor_id, "MVR")
    assert balance_vend == Decimal("1000.00")

    # 4. Verify SHADOW Entry
    events = [b["event_type"] for b in shadow_core.chain]
    assert "upos.payment.execute.completed" in events

    # Verify Global Event Partition
    global_events = [e["type"] for e in events_core.partitions["GLOBAL"]]
    assert "REVENUE_CAPTURED" in global_events

def test_upos_rejects_negative_transaction(auth_headers):
    """Security: Fail-closed on invalid amounts."""
    order_payload = {"amount": -50.0, "vendor_id": "VEND-1"}
    resp = client.post("/upos/order/create", json=order_payload, headers=auth_headers)
    assert resp.status_code == 500
    assert "Transaction amount must be positive" in resp.json()["detail"]
