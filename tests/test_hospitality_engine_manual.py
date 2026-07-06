import sys
import os

# Add the current directory to sys.path to ensure imports work
sys.path.insert(0, os.getcwd())

from mnos.modules.hospitality.engine import LowCostHospitalityEngine
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard

def setup_engine():
    shadow = ShadowLedger()
    events = DistributedEventBus()
    fce = FCEEngine()
    identity = AegisIdentityCore(shadow, events)
    policy = IdentityPolicyEngine(identity)

    # Bootstrap admin
    identity.profiles["admin"] = {
        "identity_id": "admin",
        "profile_type": "admin",
        "verification_status": "verified"
    }

    # Bootstrap roles for industry tests
    identity.profiles["airline_staff_1"] = {"identity_id": "airline_staff_1", "profile_type": "airline_partner", "verification_status": "verified"}
    identity.profiles["doctor_1"] = {"identity_id": "doctor_1", "profile_type": "medical_worker", "verification_status": "verified"}
    identity.profiles["tourist_1"] = {"identity_id": "tourist_1", "profile_type": "tourist", "verification_status": "verified"}
    identity.profiles["t1"] = {"identity_id": "t1", "profile_type": "tourist", "verification_status": "verified"}

    guard = ExecutionGuard(identity, policy, fce, shadow, events)
    imoxon = ImoxonCore(guard, fce, shadow, events)
    engine = LowCostHospitalityEngine(imoxon)

    admin_ctx = {"identity_id": "admin", "device_id": "dev1", "role": "admin"}
    engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

    return engine

def test_airline_partner_discount():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "airline_staff_1", "device_id": "phone_1", "role": "airline_partner"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 2, "amenities": ["aircon"]})
    assert booking["discount_applied"] == 25.0
    # Recalculated with Green Tax:
    # subtotal_usd = (50*2) - 25 + 10 = 85 USD
    # subtotal_mvr = 85 * 15.42 = 1310.7
    # FCE.calculate_local_order(1310.7, "TOURISM", 12.0)
    # SC(10%) = 131.07
    # Subtotal = 1441.77
    # TGST(17%) = 245.10
    # GreenTax(MVR) = 12 * 15.42 = 185.04
    # Total = 1441.77 + 245.10 + 185.04 = 1871.91
    assert booking["pricing"]["total"] == 1871.91
    print("test_airline_partner_discount PASSED")

def test_medical_worker_discount():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "doctor_1", "device_id": "phone_2", "role": "medical_worker"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["discount_applied"] == 10.0
    # subtotal_usd = (50*1) - 10 = 40 USD
    # subtotal_mvr = 40 * 15.42 = 616.8
    # SC(10%) = 61.68
    # Subtotal = 678.48
    # TGST(17%) = 115.34
    # GreenTax(MVR) = 6 * 15.42 = 92.52
    # Total = 678.48 + 115.34 + 92.52 = 886.34
    assert booking["pricing"]["total"] == 886.34
    print("test_medical_worker_discount PASSED")

def test_regular_user_no_discount():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "tourist_1", "device_id": "phone_3", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["discount_applied"] == 0.0
    # subtotal_usd = 50 USD
    # subtotal_mvr = 50 * 15.42 = 771.0
    # SC(10%) = 77.10
    # Subtotal = 848.10
    # TGST(17%) = 144.18
    # GreenTax(MVR) = 92.52
    # Total = 848.10 + 144.18 + 92.52 = 1084.8
    assert booking["pricing"]["total"] == 1084.8
    print("test_regular_user_no_discount PASSED")

def test_maldives_taxes_applied():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "t1", "device_id": "d1", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    assert booking["pricing"]["total"] == 1084.8
    print("test_maldives_taxes_applied PASSED")

if __name__ == "__main__":
    try:
        test_airline_partner_discount()
        test_medical_worker_discount()
        test_regular_user_no_discount()
        test_maldives_taxes_applied()
        print("All tests PASSED")
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
