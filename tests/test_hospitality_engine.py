import pytest
from mnos.modules.hospitality.engine import LowCostHospitalityEngine
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard

@pytest.fixture
def setup_engine():
    shadow = ShadowLedger()
    events = DistributedEventBus()
    fce = FCEEngine()
    identity = AegisIdentityCore(shadow, events)
    policy = IdentityPolicyEngine(identity)

    # We use a real guard but simplified for testing if needed
    guard = ExecutionGuard(identity, policy, fce, shadow, events)
    imoxon = ImoxonCore(guard, fce, shadow, events)
    engine = LowCostHospitalityEngine(imoxon)

    # Register identities in core
    admin_id = identity.create_profile({"full_name": "Admin", "profile_type": "admin"})
    identity.verify_identity(admin_id, "SYS")

    # Register a test property
    admin_ctx = {"identity_id": admin_id, "device_id": "dev1", "role": "admin"}
    engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0, "type": "GUESTHOUSE"})

    return engine, imoxon, identity

def test_airline_partner_discount(setup_engine):
    engine, imoxon, identity = setup_engine
    prop_id = list(engine.properties.keys())[0]

    uid = identity.create_profile({"full_name": "Staff 1", "profile_type": "airline_partner"})
    actor_ctx = {
        "identity_id": uid,
        "device_id": "phone_1",
        "role": "airline_partner"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 2,
        "amenities": ["aircon"]
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 25.0

def test_medical_worker_discount(setup_engine):
    engine, imoxon, identity = setup_engine
    prop_id = list(engine.properties.keys())[0]

    uid = identity.create_profile({"full_name": "Doc 1", "profile_type": "medical_worker"})
    actor_ctx = {
        "identity_id": uid,
        "device_id": "phone_2",
        "role": "medical_worker"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 10.0

def test_regular_user_no_discount(setup_engine):
    engine, imoxon, identity = setup_engine
    prop_id = list(engine.properties.keys())[0]

    uid = identity.create_profile({"full_name": "Tourist 1", "profile_type": "tourist"})
    actor_ctx = {
        "identity_id": uid,
        "device_id": "phone_3",
        "role": "tourist"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 0.0

def test_maldives_taxes_applied(setup_engine):
    engine, imoxon, identity = setup_engine
    prop_id = list(engine.properties.keys())[0]

    uid = identity.create_profile({"full_name": "T1", "profile_type": "tourist"})
    actor_ctx = {"identity_id": uid, "device_id": "d1", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})

    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    # Green tax:  * 1 night * 15.42 = 92.52
    assert booking["pricing"]["green_tax"] == 92.52
