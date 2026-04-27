import pytest
from fastapi.testclient import TestClient
from main import app, guard, identity_core, shadow_core, pms_folio

client = TestClient(app)

@pytest.fixture
def auth_headers():
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "PMS Staff", "profile_type": "staff"})
        did = identity_core.bind_device(uid, {"fingerprint": "pms-tab-01"})
        identity_core.verify_identity(uid, "system")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_green_tax_mira_compliance(auth_headers):
    import uuid
    guest_id = f"guest-{uuid.uuid4().hex[:6]}"
    folio = client.get(f"/pms/folio/guest/{guest_id}", headers=auth_headers).json()
    folio_id = folio["id"]

    payload = {
        "folio_id": folio_id,
        "category": "ROOM",
        "description": "3 Nights - Deluxe Room",
        "amount": 3000.0,
        "pax_count": 2,
        "nights": 3
    }

    res = client.post("/pms/folio/charge", json=payload, headers=auth_headers)
    assert res.status_code == 200
    charge = res.json()

    assert charge["green_tax_amount"] == 555.12
    assert charge["line_total"] == 4416.12

def test_immutable_reversal(auth_headers):
    import uuid
    guest_id = f"guest-{uuid.uuid4().hex[:6]}"
    folio = client.get(f"/pms/folio/guest/{guest_id}", headers=auth_headers).json()
    folio_id = folio["id"]

    charge = client.post("/pms/folio/charge", json={
        "folio_id": folio_id,
        "description": "Mini Bar",
        "amount": 500.0,
        "category": "FB"
    }, headers=auth_headers).json()

    charge_id = charge["id"]
    f1 = client.get(f"/pms/folio/{folio_id}", headers=auth_headers).json()
    initial_total = f1["total_amount"]

    rev_res = client.post("/pms/folio/charge/reversal", json={
        "charge_id": charge_id,
        "reason_code": "STAFF_MISTAKE",
        "approver_id": "manager-01"
    }, headers=auth_headers)

    assert rev_res.status_code == 200
    reversal = rev_res.json()

    assert reversal["line_total"] == -charge["line_total"]
    assert reversal["is_reversal"] is True

    updated_folio = client.get(f"/pms/folio/{folio_id}", headers=auth_headers).json()
    assert abs(updated_folio["total_amount"] - (initial_total - charge["line_total"])) < 0.01

def test_partial_settlement_states(auth_headers):
    import uuid
    guest_id = f"guest-{uuid.uuid4().hex[:6]}"
    folio = client.get(f"/pms/folio/guest/{guest_id}", headers=auth_headers).json()
    folio_id = folio["id"]

    client.post("/pms/folio/charge", json={
        "folio_id": folio_id,
        "description": "Dinner",
        "amount": 1000.0,
        "category": "FB"
    }, headers=auth_headers)

    client.post("/pms/folio/payment", json={
        "folio_id": folio_id,
        "amount": 500.0,
        "method": "CARD"
    }, headers=auth_headers)

    updated1 = client.get(f"/pms/folio/{folio_id}", headers=auth_headers).json()
    assert updated1["status"] == "PARTIALLY_SETTLED"

    client.post("/pms/folio/payment", json={
        "folio_id": folio_id,
        "amount": updated1["balance_due"],
        "method": "CASH"
    }, headers=auth_headers)

    final = client.get(f"/pms/folio/{folio_id}", headers=auth_headers).json()
    assert final["status"] == "SETTLED"
    assert final["balance_due"] == 0.0

def test_forensic_audit_trail(auth_headers):
    import uuid
    uid = auth_headers["X-AEGIS-IDENTITY"]
    guest_id = f"guest-{uuid.uuid4().hex[:6]}"

    folio = client.get(f"/pms/folio/guest/{guest_id}", headers=auth_headers).json()
    folio_id = folio["id"]

    initial_len = len(shadow_core.chain)

    client.post("/pms/folio/charge", json={
        "folio_id": folio_id,
        "description": "Audit Test",
        "amount": 100.0,
        "geo_location": {"lat": 3.2, "lng": 73.2}
    }, headers=auth_headers)

    block = next(b for b in shadow_core.chain[initial_len:] if b["event_type"] == "pms.folio.post_charge.completed")
    charge_result = block["payload"]["result"]

    assert charge_result["actor_identity"]["staff_id"] == uid
