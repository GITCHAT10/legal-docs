import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add mnos to path
sys.path.append(os.getcwd())

# Ensure NEXGEN_SECRET is set for tests
os.environ["NEXGEN_SECRET"] = "TEST-SECRET"

from main import app, identity_core, upos_core, u_storage, u_clearance

client = TestClient(app)

@pytest.fixture
def setup_identity():
    # Setup some identities in the core
    admin_id = identity_core.create_profile({"full_name": "Admin User", "profile_type": "admin"})
    guest_id = identity_core.create_profile({"full_name": "Guest User", "profile_type": "guest"})
    identity_core.verify_identity(admin_id, "SYSTEM")
    admin_dev = identity_core.bind_device(admin_id, {"fingerprint": "dev-01"})
    guest_dev = identity_core.bind_device(guest_id, {"fingerprint": "dev-02"})
    return {
        "admin": admin_id, "admin_dev": admin_dev,
        "guest": guest_id, "guest_dev": guest_dev
    }

def test_shopping_search(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["guest"], "X-AEGIS-DEVICE": setup_identity["guest_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["guest"]}
    response = client.get("/upos/global/shopping/search?q=towels", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert "estimated_landed_total" in results[0]
    assert "disclaimer" in results[0]

def test_unpaid_order_blocked_at_hub(setup_identity):
    guest_id = setup_identity["guest"]
    headers = {"X-AEGIS-IDENTITY": guest_id, "X-AEGIS-DEVICE": setup_identity["guest_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + guest_id}

    # 1. Create order but don't pay
    payload = {"amount": 1000, "tenant_id": "T1", "items": [{"id": "P1", "qty": 1}]}
    resp = client.post("/upos/global/orders/create", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    order_id = resp.json()["id"]

    # 2. Try to receive at hub as admin
    admin_headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": setup_identity["admin_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}
    receive_payload = {"quantity": 1, "photo_url": "http://img.url"}

    # This should fail based on doctrine
    with pytest.raises(PermissionError) as excinfo:
        u_storage.receive_package(admin_headers, order_id, "CHINA_HUB", receive_payload)
    assert "DOCTRINE REJECTION: Hub receiving blocked for unpaid order" in str(excinfo.value)

def test_paid_order_allowed_at_hub(setup_identity):
    guest_id = setup_identity["guest"]
    headers = {"X-AEGIS-IDENTITY": guest_id, "X-AEGIS-DEVICE": setup_identity["guest_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + guest_id}

    # 1. Create order
    payload = {"amount": 1000, "tenant_id": "T1", "items": [{"id": "P1", "qty": 1}]}
    resp = client.post("/upos/global/orders/create", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    order_id = resp.json()["id"]

    # 2. Pay order
    pay_ctx = {
        "identity_id": guest_id,
        "device_id": setup_identity["guest_dev"],
        "role": "guest"
    }
    upos_core.process_payment(pay_ctx, order_id, "WALLET")

    # 3. Receive at hub
    admin_headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": setup_identity["admin_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}
    receive_payload = {"quantity": 1, "photo_url": "http://img.url"}
    pkg = u_storage.receive_package(admin_headers, order_id, "CHINA_HUB", receive_payload)
    assert pkg["status"] == "RECEIVED_AT_HUB"

def test_port_release_gate(setup_identity):
    admin_headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": setup_identity["admin_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}

    # Initiate clearance
    job = u_clearance.initiate_clearance(admin_headers, "SHIP-001")
    job_id = job["id"]

    # Try to approve customs release without docs
    with pytest.raises(PermissionError) as excinfo:
        u_clearance.approve_customs_release(admin_headers, job_id)
    assert "GLOBAL GATE: No Customs submission without required document checklist." in str(excinfo.value)

    # Upload docs
    u_clearance.upload_document(admin_headers, job_id, "commercial_invoice", "hash1")
    u_clearance.upload_document(admin_headers, job_id, "packing_list", "hash2")
    u_clearance.upload_document(admin_headers, job_id, "bill_of_lading", "hash3")
    u_clearance.upload_document(admin_headers, job_id, "delivery_order", "hash4")
    u_clearance.upload_document(admin_headers, job_id, "customs_payment_receipt", "hash5")
    u_clearance.upload_document(admin_headers, job_id, "mpl_invoice", "hash6")
    client.post(f"/upos/global/clearance/validate-docs?job_id={job_id}", headers=admin_headers)

    # Try to approve port release before customs
    with pytest.raises(PermissionError) as excinfo:
        u_clearance.approve_port_release(admin_headers, job_id)
    assert "DOCTRINE REJECTION: No port release without Customs release." in str(excinfo.value)

    # Approve customs then port
    u_clearance.approve_customs_release(admin_headers, job_id)
    u_clearance.approve_port_release(admin_headers, job_id)
    assert u_clearance.clearance_jobs[job_id]["port_released"] == True

def test_smart_corridor_gates(setup_identity):
    from main import u_corridors, upos_core
    admin_id = setup_identity["admin"]
    guest_id = setup_identity["guest"]
    admin_headers = {"identity_id": admin_id, "device_id": setup_identity["admin_dev"], "role": "admin"}
    guest_headers = {"identity_id": guest_id, "device_id": setup_identity["guest_dev"], "role": "guest"}

    # 1. Register operator & vessel & captain
    op = u_corridors.register_operator(admin_headers, {"name": "Maldives Fast Freight"})
    ves = u_corridors.register_vessel(admin_headers, {"name": "Speedy Dhoni", "operator_id": op["id"], "type": "DHONI"})
    capt = u_corridors.register_captain(admin_headers, {"aegis_id": "capt-01", "vessel_id": ves["id"]})

    # 2. Create manifest
    manifest = u_corridors.create_manifest(admin_headers, {
        "operator_id": op["id"],
        "vessel_id": ves["id"],
        "captain_id": capt["id"],
        "route_id": "R1"
    })

    # 3. Try to load unpaid cargo
    payload = {"amount": 500, "tenant_id": "T1", "items": [{"id": "P1", "qty": 1}]}
    resp = client.post("/upos/global/orders/create", json=payload, headers={"X-AEGIS-IDENTITY": guest_id, "X-AEGIS-DEVICE": setup_identity["guest_dev"], "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + guest_id})
    assert resp.status_code == 200, resp.text
    order_id = resp.json()["id"]

    with pytest.raises(PermissionError) as excinfo:
        u_corridors.load_cargo(admin_headers, manifest["id"], {"order_id": order_id})
    assert "HARD GATE: No cargo loading without paid/FCE-approved order." in str(excinfo.value)

    # 4. Pay and load
    upos_core.process_payment(guest_headers, order_id, "CASH")
    u_corridors.load_cargo(admin_headers, manifest["id"], {"order_id": order_id})
    assert len(u_corridors.manifests[manifest["id"]]["cargo"]) == 1

def test_landed_cost_calculation():
    from mnos.modules.customs.engine import UCustomsEngine
    from mnos.modules.port.engine import UPortEngine

    customs = UCustomsEngine(None)
    port = UPortEngine(None)

    prod = {"base_price": 1000.0, "hs_code": "6302.6000"} # 20% duty
    freight = 200.0

    c_res = customs.calculate_landed_cost(prod, freight)
    # CIF = 1000 + 200 + (1000 * 0.01) = 1210
    # Duty = 1210 * 0.20 = 242
    # GST = (1210 + 242) * 0.08 = 116.16
    assert c_res["cif_value"] == 1210.0
    assert c_res["duty_estimate"] == 242.0
    assert round(c_res["import_gst_estimate"], 2) == 116.16
