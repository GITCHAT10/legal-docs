import pytest
from mnos.modules.hospitality.engine import LowCostHospitalityEngine
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context

def setup_engine():
    shadow = ShadowLedger()
    events = DistributedEventBus()
    fce = FCEEngine()
    identity = AegisIdentityCore(shadow, events)
    policy = IdentityPolicyEngine(identity)

    # Use sovereign context for setup
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})

    try:
        guard = ExecutionGuard(identity, policy, fce, shadow, events)
        imoxon = ImoxonCore(guard, fce, shadow, events)
        engine = LowCostHospitalityEngine(imoxon)

        # Register a test property
        admin_id = identity.create_profile({"full_name": "Admin", "profile_type": "admin"})
        identity.verify_identity(admin_id, "SYSTEM")
        admin_device = identity.bind_device(admin_id, {"fingerprint": "dev1"})

        admin_ctx = {"identity_id": admin_id, "device_id": admin_device, "role": "admin"}
        engine.register_property(admin_ctx, {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0})

        return engine, imoxon, identity
    finally:
        _sovereign_context.reset(token)

def test_airline_partner_discount():
    engine, imoxon, identity = setup_engine()
    prop_id = list(engine.properties.keys())[0]

    # Setup actor in registry
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        aid = identity.create_profile({"full_name": "Airliner", "profile_type": "airline_partner"})
        did = identity.bind_device(aid, {"fingerprint": "phone_1"})
    finally:
        _sovereign_context.reset(token)

    actor_ctx = {
        "identity_id": aid,
        "device_id": did,
        "role": "airline_partner"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 2,
        "amenities": ["aircon"]
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 25.0
    assert booking["pricing"]["base"] == 1310.70

def test_medical_worker_discount():
    engine, imoxon, identity = setup_engine()
    prop_id = list(engine.properties.keys())[0]

    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        aid = identity.create_profile({"full_name": "Doctor", "profile_type": "medical_worker"})
        did = identity.bind_device(aid, {"fingerprint": "phone_2"})
    finally:
        _sovereign_context.reset(token)

    actor_ctx = {
        "identity_id": aid,
        "device_id": did,
        "role": "medical_worker"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 10.0
    assert booking["pricing"]["base"] == 616.80

def test_regular_user_no_discount():
    engine, imoxon, identity = setup_engine()
    prop_id = list(engine.properties.keys())[0]

    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        aid = identity.create_profile({"full_name": "Tourist", "profile_type": "tourist"})
        did = identity.bind_device(aid, {"fingerprint": "phone_3"})
    finally:
        _sovereign_context.reset(token)

    actor_ctx = {
        "identity_id": aid,
        "device_id": did,
        "role": "tourist"
    }

    booking_data = {
        "property_id": prop_id,
        "nights": 1
    }

    booking = engine.book_stay(actor_ctx, booking_data)
    assert booking["discount_applied"] == 0.0
    assert booking["pricing"]["base"] == 771.0

def test_maldives_taxes_applied():
    engine, imoxon, identity = setup_engine()
    prop_id = list(engine.properties.keys())[0]

    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        aid = identity.create_profile({"full_name": "T1", "profile_type": "tourist"})
        did = identity.bind_device(aid, {"fingerprint": "d1"})
    finally:
        _sovereign_context.reset(token)

    actor_ctx = {"identity_id": aid, "device_id": did, "role": "tourist"}
    booking = engine.book_stay(actor_ctx, {"property_id": prop_id, "nights": 1})

    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    assert booking["pricing"]["green_tax"] == 92.52
    assert booking["pricing"]["total"] == 1084.80
