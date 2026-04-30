from typing import Any, Dict
from mnos.modules.prestige.config import get_model_for_capability

class BasePrestigeAgent:
    def __init__(self, agent_id: str, core_system: Any):
        self.agent_id = agent_id
        self.core = core_system

    async def execute_task(self, task_data: Dict) -> Dict:
        raise NotImplementedError("Subclasses must implement execute_task")

    def get_capability_model(self, capability: str) -> str:
        return get_model_for_capability(capability)
