import pytest
from fastapi.testclient import TestClient
import uuid
import os
import mnos.shared.execution_guard as eg

# Set dummy secret
os.environ["NEXGEN_SECRET"] = "TEST-SECRET"

from main import app, identity_core, guard, shadow_core

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_auth():
    # Authorize setup
    eg._sovereign_context.set({"token": "setup", "actor": {"identity_id": "system", "device_id": "sys"}})
    yield
    eg._sovereign_context.set(None)

def test_no_trace_id_no_transfer():
    """
    Core Doctrine: Every transfer requires trace_id.
    """
    identity_id = "test-actor-1"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-1",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

    identity_core.profiles[identity_id] = {
        "identity_id": identity_id,
        "profile_type": "B2C_GUEST",
        "verification_status": "verified",
        "organization_id": "TEST",
        "assigned_island": "MALE",
        "persistent_identity_hash": "hash1"
    }
    identity_core.devices["dev-1"] = {"identity_id": identity_id}

    response = client.post("/imoxon/ut/bookings/intent", json={"amount": 100}, headers=headers)
    assert response.status_code == 400
    assert "NO_TRACE_ID_NO_TRANSFER" in response.json()["detail"]

def test_esg_csr_one_usd_split_50_50():
    """
    Core Doctrine: ESG/CSR $1 split works.
    """
    identity_id = "test-actor-2"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-2",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

    # Use verified role to pass any policy checks
    identity_core.profiles[identity_id] = {
        "identity_id": identity_id,
        "profile_type": "B2C_GUEST",
        "verification_status": "verified",
        "organization_id": "TEST",
        "assigned_island": "MALE",
        "persistent_identity_hash": "hash2"
    }
    identity_core.devices["dev-2"] = {"identity_id": identity_id}

    trace_id = str(uuid.uuid4())
    # The 403 might be from ExecutionGuard rejecting because of some policy.
    # But intent creation doesn't have strict policy in the provided IdentityPolicyEngine
    # UNLESS it falls into some category.

    # Wait, the failure in the previous run for THIS test was 403.
    # In test_no_orca_no_settlement it was also 403, but I matched the detail.

    response = client.post("/imoxon/ut/bookings/intent", json={"amount": 100, "trace_id": trace_id}, headers=headers)
    if response.status_code == 403:
        print(f"DEBUG: 403 detail: {response.json()}")
    assert response.status_code == 200
    data = response.json()

    assert data["quote"]["esg_csr_fee"] == 15.42

    booking_id = data["booking_id"]
    confirm_resp = client.post(f"/imoxon/ut/bookings/confirm?booking_id={booking_id}", headers=headers)
    assert confirm_resp.status_code == 200
    splits = confirm_resp.json()["splits"]

    esg_split = next(s for s in splits if s["ledger"] == "ESG_MARINE")
    csr_split = next(s for s in splits if s["ledger"] == "CSR_TRAINING")

    assert esg_split["amount"] == 7.71
    assert csr_split["amount"] == 7.71

def test_no_orca_no_settlement():
    """
    Core Doctrine: Payout blocked without ORCA validation.
    """
    identity_id = "test-actor-3"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-3",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

    identity_core.profiles[identity_id] = {
        "identity_id": identity_id,
        "profile_type": "UT_FINANCE",
        "verification_status": "verified",
        "organization_id": "TEST",
        "assigned_island": "MALE",
        "persistent_identity_hash": "hash3"
    }
    identity_core.devices["dev-3"] = {"identity_id": identity_id}

    response = client.post("/imoxon/ut/fce/payout/release?quote_id=any&orca=false&shadow=true&apollo=true", headers=headers)
    assert response.status_code == 403
    assert "PAYOUT BLOCKED" in response.json()["detail"]
