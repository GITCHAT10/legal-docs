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
    assert booking["pricing"]["base"] == 1310.70
    print("test_airline_partner_discount PASSED")

def test_medical_worker_discount():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "doctor_1", "device_id": "phone_2", "role": "medical_worker"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["discount_applied"] == 10.0
    assert booking["pricing"]["base"] == 616.80
    print("test_medical_worker_discount PASSED")

def test_regular_user_no_discount():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "tourist_1", "device_id": "phone_3", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["discount_applied"] == 0.0
    assert booking["pricing"]["base"] == 771.0
    print("test_regular_user_no_discount PASSED")

def test_maldives_taxes_applied():
    engine = setup_engine()
    prop_id = list(engine.properties.keys())[0]
    actor_ctx = {"identity_id": "t1", "device_id": "d1", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})
    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    assert booking["pricing"]["total"] == 992.28
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
        sys.exit(1)
