import uuid
from typing import Dict, Any, List, Optional
from mnos.modules.prestige.models import TripMasterObject

class AgentRegistry:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_id: str, agent_instance: Any, agent_type: str):
        self.agents[agent_id] = {
            "instance": agent_instance,
            "type": agent_type
        }

    def get_agent(self, agent_type: str):
        for agent in self.agents.values():
            if agent["type"] == agent_type:
                return agent["instance"]
        return None

class TripService:
    def __init__(self, core_system):
        self.core = core_system
        self.trips: Dict[str, TripMasterObject] = {}

    def build_provisional_trip(self, planner_id: str) -> TripMasterObject:
        trip_id = f"PRSTG-{uuid.uuid4().hex[:6].upper()}"
        trip = TripMasterObject(
            trip_id=trip_id,
            planner_id=planner_id
        )
        self.trips[trip_id] = trip
        return trip

    def get_trip(self, trip_id: str) -> Optional[TripMasterObject]:
        return self.trips.get(trip_id)
