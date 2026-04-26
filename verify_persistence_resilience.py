import os
import uuid
import json
from main import app, imoxon, merchant, logistics_engine, identity_core
from mnos.db.session import SessionLocal, init_db
from mnos.modules.imoxon.schemas.models import ImoxonSupplier
from mnos.modules.imoxon.logistics.models import LogisticsShipment

def verify_persistence():
    print("🚀 STARTING PERSISTENCE & RESTART RESILIENCE TEST")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "persistence-verification-secret"
    init_db()

    # 1. Create Data
    actor_id = str(uuid.uuid4())
    device_id = "test-hw-001"
    h = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": device_id}

    print("[1] Creating initial state...")
    # Manual insertion to skip guard context for setup if needed,
    # but we should use the engine to prove it works through the guard.
    # Note: identity_core.create_profile uses shadow which needs guard.
    # We'll use a BOOTSTRAP token to allow setup.
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "BOOTSTRAP", "actor": {"identity_id": actor_id, "device_id": device_id, "role": "admin"}})

    try:
        identity_core.create_profile({"full_name": "Persistence Admin", "profile_type": "admin"})
        merchant.approve_vendor({"identity_id": actor_id, "device_id": device_id, "role": "admin"}, {"did": actor_id, "business_name": "Persistent Merch"})

        shipment = logistics_engine.create_shipment(
            {"identity_id": actor_id, "device_id": device_id},
            {"supplier_id": actor_id, "origin": "CN", "destination": "MV"}
        )
        shipment_id = shipment["id"]
        print(f"    Shipment Created: {shipment_id}")
    finally:
        _sovereign_context.set(None)

    # 2. Simulate App Restart (Re-instantiate engines)
    print("[2] Simulating engine re-instantiation...")
    # Create new instances as if app restarted
    from mnos.modules.imoxon.core.engine import MerchantManager
    from mnos.modules.imoxon.logistics.engine import LogisticsEngine
    from main import guard, fce_core, shadow_core, events_core, identity_core as main_identity

    new_merchant = MerchantManager(imoxon)
    new_logistics = LogisticsEngine(guard, fce_core, shadow_core, events_core, main_identity, new_merchant)

    # 3. Verify Data Presence
    print("[3] Verifying data survives in new engine instances...")
    status = new_merchant.get_vendor_status(actor_id)
    print(f"    Merchant Status (New Instance): {status}")
    assert status == "VERIFIED"

    # Check logistics via DB directly to prove no in-memory state
    with SessionLocal() as db:
        shp = db.query(LogisticsShipment).filter(LogisticsShipment.id == shipment_id).first()
        assert shp is not None
        assert shp.status == "CREATED"
        print(f"    Shipment Status (Database): {shp.status}")

    print("-" * 60)
    print("✅ PERSISTENCE VERIFIED: NO CRITICAL IN-MEMORY STATE DETECTED")

if __name__ == "__main__":
    verify_persistence()
