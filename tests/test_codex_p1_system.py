from fastapi.testclient import TestClient
from main import app, shadow_core
from mnos.shared.execution_guard import ExecutionGuard

client = TestClient(app)

def test_public_system_handshake_rejected():
    """
    P1 REGRESSION: SYSTEM must NOT be accepted through public/direct-handshake API headers.
    """
    headers = {
        "X-AEGIS-IDENTITY": "SYSTEM",
        "X-AEGIS-DEVICE": "internal",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_SYSTEM"
    }
    resp = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert resp.status_code == 401
    assert "SYSTEM identity restricted" in resp.json()["detail"]

    # Verify shadow audit
    last_block = shadow_core.chain[-1]
    assert last_block["event_type"] == "aegis.auth.direct.failure"
    assert last_block["actor_id"] == "SYSTEM"
    assert last_block["payload"]["reason"] == "SYSTEM_NOT_ALLOWED_ON_PUBLIC_API"

def test_internal_system_authorized_context_succeeds():
    """
    P1 REGRESSION: internal Laundry/background SYSTEM authorized_context still succeeds.
    """
    from main import laundry_engine

    # SYSTEM is typically used for revenue sync or background tasks.
    # In Laundry, it might be used for internal processing.

    actor_ctx = {"identity_id": "SYSTEM", "role": "system", "device_id": "internal"}
    with ExecutionGuard.authorized_context(actor_ctx):
        # SYSTEM triggering an internal finalize for an order
        # This is allowed by PolicyEngine because it's a SYSTEM role
        res = laundry_engine.nexus.finalize_cycle(actor_ctx, "DUMMY_ORDER_ID")
        # dummy order not found, so returns None or raises 404 in API, but here we call internal
        # finalize_cycle returns None if order not found
        assert res is None

    # Verify shadow audit has SYSTEM as actor for auth success (which happens inside context setup)
    # Actually authorized_context doesn't commit to shadow by itself, it just sets the context.
    # But internal methods like finalize_cycle might.
