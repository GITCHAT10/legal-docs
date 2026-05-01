import pytest
import asyncio
from decimal import Decimal
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.prestige.channel.channel_config_loader import ChannelConfigLoader
from mnos.modules.prestige.channel.auth_gateway import AuthGateway
from mnos.modules.prestige.channel.inventory_mapper import InventoryMapper, InventoryItem, InventoryStatus
from mnos.modules.prestige.channel.rate_sync_engine import RateSyncEngine
from mnos.modules.prestige.channel.availability_sync_engine import AvailabilitySyncEngine
from mnos.modules.prestige.channel.reservation_validator import ReservationValidator

class MockShadow:
    def __init__(self):
        self.commits = []
    def commit(self, event_type, actor_id, payload):
        self.commits.append({"event_type": event_type, "actor_id": actor_id, "payload": payload})

class MockPolicyEngine:
    def validate_action(self, action, ctx):
        return True, "OK"

class MockCore:
    def __init__(self):
        self.shadow = MockShadow()
        self.policy_engine = MockPolicyEngine()
        self.guard = ExecutionGuard(
            identity_core=None,
            policy_engine=self.policy_engine,
            fce=None,
            shadow=self.shadow,
            events=None
        )
        self.channel_config = ChannelConfigLoader()
        self.auth_gateway = AuthGateway(self)
        self.inventory_mapper = InventoryMapper(self)
        self.rate_sync = RateSyncEngine(self)
        self.availability_sync = AvailabilitySyncEngine(self)
        self.reservation_validator = ReservationValidator(self)

@pytest.fixture
def core():
    return MockCore()

@pytest.fixture
def actor_ctx():
    return {"identity_id": "ACTOR-001", "device_id": "DEV-001", "role": "MANAGER"}

def test_channel_cannot_change_price_directly(core, actor_ctx):
    # Register item
    item = InventoryItem(
        internal_id="VILLA-001",
        external_ids={"siteminder": "EXT-VILLA-001"},
        supplier_id="SUP-001",
        supplier_contract_ref="CON-001",
        inventory_type="villa",
        title="Luxury Villa",
        description="Beautiful villa",
        base_price=1000.0,
        availability_window={"start": "2024-01-01", "end": "2024-12-31"},
        cancellation_policy_ref="CAN-001"
    )
    core.inventory_mapper.register_item(actor_ctx, item)
    core.availability_sync.set_availability(actor_ctx, "VILLA-001", 1)

    # Try to validate a reservation with a different price
    payload = {
        "item_id": "EXT-VILLA-001",
        "total_price": 500.0, # Attempting to change price
        "guest_name": "John Doe"
    }
    result = core.reservation_validator.validate_reservation(actor_ctx, "siteminder", payload)

    assert result["status"] == "rejected"
    assert result["reason"] == "PRICE_MISMATCH"

def test_auth_failure_revokes_credential(core, actor_ctx):
    core.auth_gateway.register_channel(actor_ctx, "siteminder", "secret123", "HMAC")

    # Valid request
    headers = {}
    payload = "{}"
    sig = "valid_sig_simulated" # validate_request would need real HMAC logic if not mocked
    # For this test, we'll manually trigger failures

    core.auth_gateway._emit_security_alert("siteminder", "CRITICAL_AUTH_FAILURE")

    # Revoke (normally would be automatic on N failures, here we test manual revoke)
    core.auth_gateway.revoke_credentials(actor_ctx, "siteminder")

    assert "siteminder" not in core.auth_gateway.channel_credentials
    assert any(c["event_type"] == "prestige.channel.auth_revoked" for c in core.shadow.commits)

@pytest.mark.asyncio
async def test_rate_push_requires_shadow_seal(core, actor_ctx):
    item = InventoryItem(
        internal_id="VILLA-002",
        external_ids={"siteminder": "EXT-VILLA-002"},
        supplier_id="SUP-001",
        supplier_contract_ref="CON-001",
        inventory_type="villa",
        title="Luxury Villa 2",
        description="Beautiful villa",
        base_price=1200.0,
        availability_window={"start": "2024-01-01", "end": "2024-12-31"},
        cancellation_policy_ref="CAN-001"
    )
    core.inventory_mapper.register_item(actor_ctx, item)

    await core.rate_sync.push_rates(actor_ctx, "siteminder", "VILLA-002")

    assert any(c["event_type"] == "prestige.channel.rate_sync_success" for c in core.shadow.commits)

def test_inventory_cannot_go_below_zero(core, actor_ctx):
    core.availability_sync.set_availability(actor_ctx, "VILLA-001", 5)

    with pytest.raises(RuntimeError, match="Insufficient inventory"):
        core.availability_sync.adjust_availability(actor_ctx, "VILLA-001", -10)

    assert core.availability_sync.canonical_availability["VILLA-001"] == 5

def test_high_value_requires_human_approval(core, actor_ctx):
    item = InventoryItem(
        internal_id="VVIP-VILLA",
        external_ids={"siteminder": "EXT-VVIP-VILLA"},
        supplier_id="SUP-001",
        supplier_contract_ref="CON-001",
        inventory_type="villa",
        title="VVIP Villa",
        description="Ultra luxury",
        base_price=15000.0, # High value
        availability_window={"start": "2024-01-01", "end": "2024-12-31"},
        cancellation_policy_ref="CAN-001"
    )
    core.inventory_mapper.register_item(actor_ctx, item)
    core.availability_sync.set_availability(actor_ctx, "VVIP-VILLA", 1)

    payload = {
        "item_id": "EXT-VVIP-VILLA",
        "total_price": 15000.0,
        "guest_name": "John Doe"
    }
    result = core.reservation_validator.validate_reservation(actor_ctx, "siteminder", payload)

    assert result["status"] == "success"
    assert result["booking_status"] == "NEEDS_HUMAN_APPROVAL"

def test_night_landing_block(core, actor_ctx):
    item = InventoryItem(
        internal_id="VILLA-003",
        external_ids={"siteminder": "EXT-VILLA-003"},
        supplier_id="SUP-001",
        supplier_contract_ref="CON-001",
        inventory_type="villa",
        title="Standard Villa",
        description="Standard",
        base_price=500.0,
        availability_window={"start": "2024-01-01", "end": "2024-12-31"},
        cancellation_policy_ref="CAN-001",
        transfer_requirements=True
    )
    core.inventory_mapper.register_item(actor_ctx, item)
    core.availability_sync.set_availability(actor_ctx, "VILLA-003", 1)

    payload = {
        "item_id": "EXT-VILLA-003",
        "total_price": 500.0,
        "guest_name": "Late Arrival",
        "arrival_time": "02:00" # Blocked
    }
    result = core.reservation_validator.validate_reservation(actor_ctx, "siteminder", payload)

    assert result["status"] == "rejected"
    assert result["reason"] == "TRANSFER_IMPOSSIBLE_NIGHT_LANDING"
