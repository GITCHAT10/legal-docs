import pytest
from mnos.modules.prestige.agents.channel_manager_agent import ChannelManagerAgent
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

@pytest.fixture
def shadow():
    return ShadowLedger()

@pytest.fixture
def auth_actor():
    return {"identity_id": "SYS", "device_id": "DEV-01", "role": "admin"}

@pytest.mark.anyio
async def test_channel_manager_agent_applies_source_priority(shadow, auth_actor):
    class MockCore:
        def __init__(self, s): self.shadow = s
    agent = ChannelManagerAgent("ch_01", MockCore(shadow))

    inventory = [
        {"id": "T1", "source": "TBO", "name": "Hotel T"},
        {"id": "D1", "source": "DIRECT_CONTRACT", "name": "Hotel D"}
    ]

    with ExecutionGuard.authorized_context(auth_actor):
        res = await agent.execute_task({"raw_inventory": inventory})
        # DIRECT_CONTRACT (index 0) should be first
        assert res["ranked_inventory"][0]["id"] == "D1"
        assert res["ranked_inventory"][1]["id"] == "T1"

@pytest.mark.anyio
async def test_channel_manager_agent_rejects_stop_sale(shadow, auth_actor):
    class MockCore:
        def __init__(self, s): self.shadow = s
    agent = ChannelManagerAgent("ch_01", MockCore(shadow))

    inventory = [
        {"id": "S1", "source": "SALA", "stop_sale": True},
        {"id": "S2", "source": "SALA", "stop_sale": False}
    ]

    with ExecutionGuard.authorized_context(auth_actor):
        res = await agent.execute_task({"raw_inventory": inventory})
        assert len(res["ranked_inventory"]) == 1
        assert res["ranked_inventory"][0]["id"] == "S2"

@pytest.mark.anyio
async def test_channel_manager_agent_restricts_p4_inventory_to_approved_agents(shadow, auth_actor):
    class MockCore:
        def __init__(self, s): self.shadow = s
    agent = ChannelManagerAgent("ch_01", MockCore(shadow))

    inventory = [
        {"id": "P4-1", "source": "DIRECT_PRIVATE_VILLA", "privacy_tier": "P4"}
    ]

    with ExecutionGuard.authorized_context(auth_actor):
        # Case 1: Standard agent tier
        res = await agent.execute_task({"raw_inventory": inventory, "agent_tier": "STANDARD"})
        assert len(res["ranked_inventory"]) == 0

        # Case 2: VIP agent tier
        res_vip = await agent.execute_task({"raw_inventory": inventory, "agent_tier": "VIP"})
        assert len(res_vip["ranked_inventory"]) == 1
        assert res_vip["ranked_inventory"][0]["id"] == "P4-1"

@pytest.mark.anyio
async def test_channel_manager_agent_requests_mac_eos_validation(shadow, auth_actor):
    class MockCore:
        def __init__(self, s): self.shadow = s
    agent = ChannelManagerAgent("ch_01", MockCore(shadow))

    with ExecutionGuard.authorized_context(auth_actor):
        res = await agent.execute_task({})
        assert res["requires_mac_eos_validation"] is True
        assert res["requires_fce_validation"] is True
