import pytest
from main import identity_core
from mnos.shared.execution_guard import ExecutionGuard

@pytest.fixture
def admin_headers():
    token = ExecutionGuard.set_system_context()
    uid = identity_core.create_profile({
        "full_name": "System Admin",
        "profile_type": "admin",
        "organization_id": "MIG-CORE"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "admin-device-secure"})
    identity_core.verify_identity(uid, "SYSTEM-BOOTSTRAP")
    ExecutionGuard.reset_context(token)
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-admin-001"
    }

@pytest.fixture
def verified_actor_headers():
    token = ExecutionGuard.set_system_context()
    uid = identity_core.create_profile({
        "full_name": "Verified Citizen",
        "profile_type": "user",
        "organization_id": "MIG-COMMUNITY"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "user-device-verified"})
    identity_core.verify_identity(uid, "GOV-PORTAL")
    ExecutionGuard.reset_context(token)
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-user-001"
    }

@pytest.fixture
def merchant_headers():
    token = ExecutionGuard.set_system_context()
    uid = identity_core.create_profile({
        "full_name": "Merchant One",
        "profile_type": "supplier",
        "organization_id": "MIG-MERCHANTS"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "merchant-pos-01"})
    identity_core.verify_identity(uid, "BANK-VERIFIER")
    ExecutionGuard.reset_context(token)
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-merchant-001"
    }

@pytest.fixture
def island_gm_headers():
    token = ExecutionGuard.set_system_context()
    uid = identity_core.create_profile({
        "full_name": "Maafushi GM",
        "profile_type": "island_gm",
        "assigned_island": "Maafushi",
        "organization_id": "MIG-ISLANDS"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "gm-tablet-secure"})
    identity_core.verify_identity(uid, "MINISTRY-INTERNAL")
    ExecutionGuard.reset_context(token)
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-gm-001"
    }

@pytest.fixture
def b2b_agent_headers():
    token = ExecutionGuard.set_system_context()
    uid = identity_core.create_profile({
        "full_name": "B2B Agent",
        "profile_type": "b2b_agent",
        "organization_id": "GLOBAL-TO"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "agent-device-secure"})
    identity_core.verify_identity(uid, "B2B-VERIFIER")
    ExecutionGuard.reset_context(token)
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-b2b-001"
    }

@pytest.fixture
def system_headers():
    # Create a system profile in AEGIS to satisfy registry check
    uid = "SYSTEM"
    if uid not in identity_core.profiles:
        identity_core.profiles[uid] = {
            "identity_id": uid,
            "profile_type": "admin",
            "organization_id": "CORE",
            "verification_status": "verified"
        }
    did = "KERNEL-GATE"
    identity_core.devices[did] = {"device_id": did, "identity_id": uid}

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-TRACE-ID": "trace-sys-001"
    }
