import pytest
from mnos.modules.hospitality.engine import LowCostHospitalityEngine
from mnos.shared.execution_guard import ExecutionGuard, set_system_context, _sovereign_context
from main import identity_core, policy_engine, fce_core, shadow_core, events_core, imoxon

def setup_engine():
    return LowCostHospitalityEngine(imoxon)

def get_headers(full_name, profile_type):
    set_system_context()
    try:
        identity_id = identity_core.create_profile({"full_name": full_name, "profile_type": profile_type})
        device_id = identity_core.bind_device(identity_id, {"fingerprint": "test"})
        identity_core.verify_identity(identity_id, "SYSTEM")
        return {"identity_id": identity_id, "device_id": device_id, "role": profile_type}
    finally:
        _sovereign_context.set(None)

def test_airline_partner_discount():
    engine = setup_engine()
    admin_ctx = get_headers("Admin", "admin")
    airline_ctx = get_headers("Airline Staff", "airline_partner")

    prop = engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

    booking = engine.book_stay(airline_ctx, {"property_id": prop["id"], "nights": 1})
    # airline_partner = 25% off -> 50 * 0.75 = 37.5
    assert booking["discount_applied"] == 12.5
    assert booking["base_usd"] == 50.0

def test_medical_worker_discount():
    engine = setup_engine()
    admin_ctx = get_headers("Admin", "admin")
    medical_ctx = get_headers("Dr. Ahmed", "medical_worker")

    prop = engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

    booking = engine.book_stay(medical_ctx, {"property_id": prop["id"], "nights": 1})
    # medical_worker = 20% off -> 50 * 0.80 = 40.0
    assert booking["discount_applied"] == 10.0

def test_regular_user_no_discount():
    engine = setup_engine()
    admin_ctx = get_headers("Admin", "admin")
    user_ctx = get_headers("Guest", "user")

    prop = engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

    booking = engine.book_stay(user_ctx, {"property_id": prop["id"], "nights": 1})
    assert booking["discount_applied"] == 0.0

def test_maldives_taxes_applied():
    engine = setup_engine()
    admin_ctx = get_headers("Admin", "admin")
    user_ctx = get_headers("Guest", "user")

    prop = engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 100.0})

    booking = engine.book_stay(user_ctx, {"property_id": prop["id"], "nights": 1})
    # Base 100 USD -> 1542 MVR
    # 1542 + 10% SC (154.2) = 1696.2
    # 1696.2 + 17% TGST (288.35) = 1984.55
    # Green Tax (Guesthouse ) -> 6 * 15.42 = 92.52
    # Total = 1984.55 + 92.52 = 2077.07
    assert booking["pricing"]["total"] == 2077.07
