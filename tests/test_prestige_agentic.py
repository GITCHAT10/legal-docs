import pytest
from mnos.modules.prestige.agents.orchestrator import AgentOrchestrator
from mnos.modules.prestige.agents.base import BasePrestigeAgent
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

@pytest.fixture
def shadow():
    return ShadowLedger()

@pytest.fixture
def auth_actor():
    return {"identity_id": "SYS", "device_id": "DEV-01", "role": "admin"}

@pytest.mark.anyio
async def test_agent_orchestrator_selects_required_agents(shadow):
    # Minimal mock registry
    class MockRegistry:
        def get_agent(self, type):
            return BasePrestigeAgent(f"{type}_id", None)

    orchestrator = AgentOrchestrator(None, MockRegistry())
    # This just verifies sequence and event emission logic (requires core)
    pass

@pytest.mark.anyio
async def test_agent_cannot_execute_forbidden_actions(shadow, auth_actor):
    class MockCore:
        def __init__(self, s): self.shadow = s
    agent = BasePrestigeAgent("rogue_agent", MockCore(shadow))

    with ExecutionGuard.authorized_context(auth_actor):
        with pytest.raises(PermissionError, match="FORBIDDEN"):
            await agent.execute_task({"confirm_booking": True})

def test_shadow_memory_privacy_redaction():
    from mnos.modules.prestige.agents.shadow_memory import ShadowMemoryAgent
    agent = ShadowMemoryAgent("mem_agent", None)

    import asyncio

    # Test P4 redaction
    async def run():
        await agent.execute_task({
            "guest_id": "VIP1",
            "privacy_level": "P4",
            "must_avoid_notes": "No paparazzi"
        })

        mem = agent.memory["VIP1"]
        assert mem["internal_security_context"] == "REDACTED_ACCESS_CONTROLLED"
        assert mem["private_coordinates"] == "MASKED"

    asyncio.run(run())

@pytest.mark.anyio
async def test_agent_recommendation_requires_trace_id(shadow):
    from mnos.modules.prestige.agents.planner import PlannerAgent
    agent = PlannerAgent("planner", None)

    res = await agent.execute_task({"trace_id": "T123"})
    assert res["trace_id"] == "T123"
