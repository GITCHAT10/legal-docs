from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict, Any, List

class ChannelManagerAgent(BasePrestigeAgent):
    async def _run_agent_logic(self, task_data: Dict) -> Dict:
        """
        ChannelManagerAgent: Reasons over inventory, rate plans, source priority.
        """
        trace_id = task_data.get("trace_id", "UNTRACTED")
        self.core.shadow.commit("prestige.agentic.channel_manager_selected", self.agent_id, {"trace_id": trace_id})

        # 1. Source Priority logic
        source_priority = [
            "DIRECT_CONTRACT", "SALA", "DIRECT_GUESTHOUSE",
            "DIRECT_PRIVATE_VILLA", "TBO", "RATEHAWK",
            "HOTELBEDS", "MANUAL_ALLOTMENT"
        ]

        # 2. Filter & Rank (Simulated)
        inventory = task_data.get("raw_inventory", [])
        ranked = []
        for item in inventory:
            # Filter stop-sale
            if item.get("stop_sale"):
                self.core.shadow.commit("prestige.agentic.channel_stop_sale_rejected", self.agent_id, {"item_id": item.get("id")})
                continue

            # Agent distribution rules (P3/P4 restriction)
            agent_tier = task_data.get("agent_tier", "STANDARD")
            if item.get("privacy_tier") in ["P3", "P4"] and agent_tier != "VIP":
                self.core.shadow.commit("prestige.agentic.channel_agent_access_filtered", self.agent_id, {"item_id": item.get("id"), "reason": "UNAUTHORIZED_TIER"})
                continue

            ranked.append(item)

        # Sort by priority
        ranked.sort(key=lambda x: source_priority.index(x.get("source", "MANUAL_ALLOTMENT")))
        self.core.shadow.commit("prestige.agentic.channel_inventory_ranked", self.agent_id, {"count": len(ranked)})

        # 3. Validation requests (preparing for next layers)
        return {
            "agent": self.agent_id,
            "status": "channel_options_prepared",
            "ranked_inventory": ranked,
            "provisional_allocation": True,
            "requires_mac_eos_validation": True,
            "requires_ut_feasibility": any(i.get("requires_transfer") for i in ranked),
            "requires_fce_validation": True
        }
