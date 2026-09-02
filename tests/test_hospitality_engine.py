import pytest
from mnos.modules.hospitality.engine import LowCostHospitalityEngine
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard

class MockGuard:
    def __init__(self, policy_engine):
        self.policy_engine = policy_engine

    def execute_sovereign_action(self, action_type, actor_ctx, logic_func, *args, **kwargs):
        success, msg = self.policy_engine.validate_action(action_type, actor_ctx)
        if not success:
            raise PermissionError(msg)
        return logic_func(*args, **kwargs)

    def get_actor(self):
        return {"identity_id": "test_actor"}

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

    # Register a test property with verified identity
    admin_id = identity.create_profile({"full_name": "Admin", "profile_type": "admin"})
    identity.verify_identity(admin_id, "SYSTEM")
    admin_ctx = {"identity_id": admin_id, "device_id": "dev1", "role": "admin", "verified": True}
    engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

    return engine, imoxon

def test_airline_partner_discount(setup_engine):
    engine, imoxon = setup_engine
    prop_id = list(engine.properties.keys())[0]

    # Use authorized_context to setup verified identities
    from mnos.shared.execution_guard import authorized_context
    with authorized_context():
        aid = imoxon.guard.identity_core.create_profile({"full_name": "Airline Staff", "profile_type": "airline_partner"})
        imoxon.guard.identity_core.verify_identity(aid, "SYSTEM")

    actor_ctx = {
        "identity_id": aid,
        "device_id": "phone_1",
        "role": "airline_partner"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 2,
        "amenities": ["aircon"]
    }

    booking = engine.book_stay(actor_ctx, booking_data)

    # Base: 50 * 2 = 100 USD
    # Discount: 25% of 100 = 25 USD
    # Amenity: 10 USD
    # Subtotal USD: 100 - 25 + 10 = 85 USD
    # Subtotal MVR: 85 * 15.42 = 1310.70 MVR

    assert booking["discount_applied"] == 25.0
    assert booking["pricing"]["base"] == 1310.70

def test_medical_worker_discount(setup_engine):
    engine, imoxon = setup_engine
    prop_id = list(engine.properties.keys())[0]

    from mnos.shared.execution_guard import authorized_context
    with authorized_context():
        mid = imoxon.guard.identity_core.create_profile({"full_name": "Doctor", "profile_type": "medical_worker"})
        imoxon.guard.identity_core.verify_identity(mid, "SYSTEM")

    actor_ctx = {
        "identity_id": mid,
        "device_id": "phone_2",
        "role": "medical_worker"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)

    # Base: 50 USD
    # Discount: 20% of 50 = 10 USD
    # Subtotal USD: 50 - 10 = 40 USD
    # Subtotal MVR: 40 * 15.42 = 616.80 MVR

    assert booking["discount_applied"] == 10.0
    assert booking["pricing"]["base"] == 616.80

def test_regular_user_no_discount(setup_engine):
    engine, imoxon = setup_engine
    prop_id = list(engine.properties.keys())[0]

    actor_ctx = {
        "identity_id": "tourist_1",
        "device_id": "phone_3",
        "role": "tourist"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)

    assert booking["discount_applied"] == 0.0
    # 50 * 15.42 = 771.0 MVR
    assert booking["pricing"]["base"] == 771.0

def test_maldives_taxes_applied(setup_engine):
    engine, imoxon = setup_engine
    prop_id = list(engine.properties.keys())[0]

    actor_ctx = {"identity_id": "t1", "device_id": "d1", "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})

    # Base MVR: 771.0
    # Service Charge: 10% = 77.10
    # Subtotal: 848.10
    # TGST (Tourism): 17% of 848.10 = 144.177 -> 144.18
    # Green Tax (assuming GUESTHOUSE type): $6 * 1 night * 15.42 = 92.52
    # Total: 848.10 + 144.18 + 92.52 = 1084.80

    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    assert booking["pricing"]["green_tax"] == 92.52
    assert booking["pricing"]["total"] == 1084.80
